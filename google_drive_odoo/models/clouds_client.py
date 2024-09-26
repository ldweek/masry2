# -*- coding: utf-8 -*-

import base64

from odoo import api, fields, models

from ..libs.google_drive_service import GoogleDriveApiClient as Client


class clouds_client(models.Model):
    """
    Overwrite to add google drive methods
    """
    _inherit = "clouds.client"

    def _default_googledrive_redirect_uri(self):
        """
        The method to return default for googledrive_redirect_uri
        """
        Config = self.env["ir.config_parameter"].sudo()
        base_odoo_url = Config.get_param("web.base.url", "http://localhost:8069")
        return "{}/google_drive_token".format(base_odoo_url)

    cloud_client = fields.Selection(
        selection_add=[("google_drive", "Google Drive")],
        required=True,
        ondelete={"google_drive": "cascade"},
    )
    googledrive_client_id = fields.Char(string="Google Drive app client ID")
    googledrive_client_secret = fields.Char(string="Google Drive app secret key")
    googledrive_redirect_uri = fields.Char(
        string="Google Drive redirect URL",
        default=_default_googledrive_redirect_uri,
        help="The same redirect URL should be set for the Google Drive app settings",
    )
    googledrive_session = fields.Char(string="Google Drive active session", readonly=True, default="")
    google_active_token = fields.Char(string="Google Drive active token", readonly=True, default="")
    googleteam_drive = fields.Boolean(
        string="Google team drive in use",
        help="Turn on if the sync should be done for a team Google Drive",
    )
    googledrive_drive = fields.Char(
        string="Google team drive name",
        help="To which team drives attachments are synced? Make sure your user has full rights to all drives inside",
    )
    google_drive_key = fields.Char(string="Google team drive key", readonly=True, default="")

    def action_google_drive_establish_connection(self):
        """
        The method to establish connection for Google Drive

        Methods:
         * _gd_get_auth_url

        Returns:
         * action window to confirm in google

        Extra info:
         * Expected singleton
        """
        auth_url = self._gd_get_auth_url()
        res = {"name": "Google Drive", "type": "ir.actions.act_url", "url": auth_url}
        return res

    ####################################################################################################################
    ##################################   LOG IN METHODS ################################################################
    ####################################################################################################################
    def _gd_get_auth_url(self):
        """
        Get URL of authentification page
         1. Clean session, if new url is required

        Methods:
         * _google_drive_get_client
         * authorization_url of Google Drive Api Client

        Returns:
         * char - url of application to log in

        Extra info:
         * Expected singleton
        """
        self.googledrive_session = "" # 1
        self._cloud_log(True, "App confirmation process was started", "DEBUG")
        gdrive_client, log_message = self._google_drive_get_client(new_token_required=True)
        if gdrive_client:
            self.error_state = False
            res = gdrive_client.authorization_url(redirect_uri=self.googledrive_redirect_uri)
        else:
            self.error_state = log_message
            res = self.env.ref("cloud_base.clouds_client_action_form_only").read()[0]
            res["res_id"] = self.id
        return res

    def _gd_create_session(self, code=False):
        """
        Authenticates to Google Drive

        Args:
         * code - authorization code received

        Methods:
         * refresh_token of Google Drive Api Client
         * get_token_from_refresh_token of Google Drive Api Client
         * _google_drive_root_directory
         * _cloud_log

        Returns:
         * tuple
          ** bool - True if authentication is done, False otherwise
          ** char - log_message

        Extra info:
         * The structure of tokens/codes is: authorization_code > refresh_token > access_token
         * Expected singleton
        """
        result = log_message = True
        api_client = self._context.get("cclients", {}).get(self.id)
        if code:
            token = api_client.refresh_token(authorization_code=code, redirect_uri=self.googledrive_redirect_uri)
            if not token:
                log_message = "Could not authenticate: check credentials"
                result = False
            else:
                self.googledrive_session = token
                api_client.get_token_from_refresh_token(
                    refresh_token=token, redirect_uri=self.googledrive_redirect_uri
                )
                result = True
                log_message = "Token was received"
        else:
            log_message = "Could not authenticate: make sure you have granted all permissions"
            result = False
        self._cloud_log(result, log_message)
        return result, log_message

    def _gd_search_drive_id(self):
        """
        Method to find drive_id in Google Drive of selected directory if it is a team drive or user drive instead

        Methods:
         * _list_team_drives of Google Drive Api Client
         * _cloud_log

        Returns:
         * tuple
          ** bool - True if authentication is done, False otherwise
          ** char - log_message

        Extra info:
         * team drive differs from individual only for optional params and file metadata. Look at -->
          https://stackoverflow.com/questions/45327769/how-can-i-create-a-folder-within-a-team-drive-with-the-google-api
         * Expected singleton
        """
        result = log_message = True
        if self.googleteam_drive:
            api_client = self._context.get("cclients", {}).get(self.id)
            try:
                drive_name = self.googledrive_drive
                drives = api_client._list_team_drives(name=drive_name)
                for prop in drives["teamDrives"]:
                    if prop["name"] == drive_name:
                        drive = prop["id"]
                        break
                else:
                    result = False
                    log_message = """The team drive wasn't found.
Make sure that drive with the name {} actually exists.
Make sure there are no extra symbols or spaces in the drive name.
Check that your user is a full-rights admin who might list the drives""".format(drive_name)
                self.google_drive_key = drive
                api_client.team_drive_id = self.googleteam_drive and self.google_drive_key or None
                result = True
                log_message = "Team drive was successfully found"
            except Exception as error:
                result = False
                log_message = """The team drive wasn't found.
Make sure that drive with the name {} actually exists.
Make sure there are no extra symbols or spaces in the drive name.
Check that your user is a full-rights admin who might list the drives.
Error: {}""".format(drive_name, error)
            self._cloud_log(result, log_message)
        return result, log_message

    def _gd_root_folder_wrapper(self):
        """
        The method to make initial setup of the root folder

        Methods:
         * _onedrive_root_directory

        Returns:
         * tuple
          ** bool - True if authentication is done, False otherwise
          ** char - log_message
        """
        root_dir = self._google_drive_root_directory()
        if root_dir:
            self.write({"state": "confirmed"})
            log_message = "Authentication was successfully done"
            result = True
        else:
            log_message = "It is not possible to authenticate: a root folder cannot be created. Check logs"
            result = False
        self._cloud_log(result, log_message)
        return result, log_message

    ####################################################################################################################
    ##################################   API methods   #################################################################
    ####################################################################################################################
    def _google_drive_get_client(self, new_token_required=False):
        """
        Method to return instance of Google Drive API Client

        Args:
         * new_token_required - bool - whether we can retrieve a token from existng auth code

        Methods:
         * get_token_from_refresh_token of Google Drive Api Client
         * _get_new_expiration
         * _cloud_log

        Returns:
         * tuple:
          ** GoogleDrive instance if initiated. False otherwise
          ** char

        Extra info:
         * Expected singleton
        """
        log_message = ""
        try:
            if self.googledrive_session and not new_token_required:
                self._cloud_log(True, "The process of initiating the client was started", "DEBUG")
            api_client = Client(self.googledrive_client_id, self.googledrive_client_secret, self)
            if self.googledrive_session and not new_token_required:
                if self.google_active_token and self.expiration_datetime > fields.Datetime.now():
                    token = api_client.token = self.google_active_token
                else:
                    token = api_client.get_token_from_refresh_token(
                        refresh_token=self.googledrive_session, redirect_uri=self.googledrive_redirect_uri,
                    )
                    self.write({
                        "google_active_token": token,
                        "expiration_datetime": self._get_new_expiration(2699), # token life = 60min - 15min for cron
                    })
                if not token:
                    log_message = "The token has expired or revoked"
                    api_client = False
                    self._cloud_log(False, log_message)
                else:
                    api_client.team_drive_id = self.googleteam_drive and self.google_drive_key or None
                    log_message = "The token was received from the refresh token"
                    self._cloud_log(True, log_message, "DEBUG")
        except Exception as er:
            api_client = False
            log_message = "It is not possible to authenticate. Reason: {}".format(er)
            self._cloud_log(False, log_message)
        return api_client, log_message

    def _google_drive_check_root_folder(self, client_id):
        """
        The method to check whether the root folder exists

        Args:
         * client_id - instance of Google Drive Api Client

        Methods:
         * _get_file_metadata of Google Drive Api Client

        Returns:
         * True

        Extra info:
         * IMPORTANT NOTE: here client is passed in args, not in context, since context is not yet updated
         * Expected singleton
        """
        log_message = ""
        res = True
        odoo_path = client_id._get_file_metadata(self.root_folder_key)
        if not odoo_path:
            res = False
            child_items = {}
            log_message = "The root folder is not available. Reconnect to create a new one"
        return res, log_message

    def _google_drive_check_api_error(self, error):
        """
        The method to get an error type based on response
 
        Args:
         * error class related to API

        Retunes:
         * int
        """
        error_type = 400
        if type(error).__name__ == "MissingError":
            error_type = 404
        return error_type

    def _google_drive_root_directory(self):
        """
        Method to return root directory name and id (create if not yet)

        Methods:
         * _check_api_error
         * _get_file_metadata of Google Drive Api Client
         * _create_folder of Google Drive Api Client
         * _cloud_log

        Returns:
         * key, name - name of folder and key in client
         * False, False if failed
        """
        client = self._context.get("cclients", {}).get(self.id)
        res_id = self.root_folder_key
        res = False
        if res_id:
            try:
                #in try, since the folder might be removed in meanwhile
                res = client._get_file_metadata(drive_id=res_id)
                self._cloud_log(True, "The root directory {},{} was successfully found".format(
                    self.root_folder_name, self.root_folder_key
                ))
            except Exception as error:
                if self._check_api_error(error) == 404:
                    res_id = False # to guarantee creation of item
                    self._cloud_log(
                        False,
                        "The root directory {}{} was removed from the clouds. Creating a new one".format(
                            self.root_folder_name, self.root_folder_key
                        ),
                        "WARNING",
                    )
                else:
                    self._cloud_log(False, "Unexpected error while searching the root directory {},{}: {}".format(
                        self.root_folder_name, self.root_folder_key, error
                    ))
                    res_id = True # to guarantee no creation of item
                    res = False
        if not res_id:
            try:
                res_id = client._create_folder(name=self.root_folder_name, parent="root").get("id")
                self.root_folder_key = res_id
                self._cloud_log(True, "The root directory {} was successfully created".format(self.root_folder_name))
                res = res_id
            except Exception as error:
                res = False
                self._cloud_log(
                    False,
                    "Unexpected error during the root directory {} creation: {}".format(self.root_folder_name, error)
                )
        return res and True or False

    def _google_drive_api_get_child_items(self, cloud_key=False):
        """
        The method to retrieve all child elements for a folder
        Note: If folder was removed, all its children were removed as well

        Args:
         * cloud_key - char

        Methods:
         * _list_children_items of Google Drive Api Client

        Returns:
         * dicts:
          ** folder_ids
          ** attachment_ids
           *** cloud_key - char (cloud key)
           *** name - char
        """
        client = self._context.get("cclients", {}).get(self.id)
        items = client._list_children_items(drive_id=cloud_key)
        attachments = []
        subfolders = []
        for child in items:
            res_vals = {"cloud_key": child.get("id"),"name": child.get("name"),}
            if child.get("mimeType") == "application/vnd.google-apps.folder":
                subfolders.append(res_vals)
            else:
                attachments.append(res_vals)
        return {"folder_ids": subfolders, "attachment_ids": attachments}

    def _google_drive_upload_attachment_from_cloud(self, folder_id, attachment_id, cloud_key, args):
        """
        Method to upload a file from cloud

        Args:
         * the same as for _call_api_method of clouds.client (cloud.base)

        Methods:
         * _download_file of Google Drive Api Client

        Returns:
         * binary (base64 decoded)
         * False if method failed
        """
        client = self._context.get("cclients", {}).get(self.id)
        result = client._download_file(drive_id=attachment_id.cloud_key)
        return result

    def _google_drive_setup_sync(self, folder_id, attachment_id, cloud_key, args):
        """
        The method to create folder in clouds

        Args:
         * the same as for _call_api_method of clouds.client (cloud.base)
         * args should contain "parent_key"

        Methods:
         * _create_folder of Google Drive Api Client

        Returns:
         * dict of values to write in clouds.folder

        Extra info:
         * setup sync assumes that a folder does not exist in client. If a folder was previously deactivated,
           it was just deleted from clouds
        """
        result =  False
        client = self._context.get("cclients", {}).get(self.id)
        result = client._create_folder(name=folder_id.name, parent=args.get("parent_key"))
        result = {"cloud_key": result.get("id"), "url": result.get("webViewLink")}
        return result

    def _google_drive_update_folder(self, folder_id, attachment_id, cloud_key, args):
        """
        Method to update folder in clouds

        Args:
         * the same as for _call_api_method of clouds.client (cloud.base)
         * in args we should receive parent_key

        Methods:
         * _move_or_update_file of Google Drive Api Client

        Returns:
         * dict of values to write in clouds folder
        """
        client = self._context.get("cclients", {}).get(self.id)
        result = client._move_or_update_file(
            drive_id=folder_id.cloud_key, new_parent=args.get("parent_key"), new_name=folder_id.name,
        )
        result = {"cloud_key": result.get("id"), "url": result.get("webViewLink")}
        return result

    def _google_drive_delete_folder(self, folder_id, attachment_id, cloud_key, args):
        """
        Method to delete folder in clouds
        The method is triggered directly from _adapt_folder_reverse (cloud_client does not have _delete_folder)
        UNDER NO CIRCUMSTANCES DO NOT DELETE THIS METHOD

        Args:
         * the same as for _call_api_method of clouds.client (cloud.base)

        Methods:
         * _delete_file of Google Drive Api Client

        Returns:
          * bool

        Extra info:
         * Actually the result of the operation is always an error. 204 if successful, so, return would never take place
        """
        result = False
        client = self._context.get("cclients", {}).get(self.id)
        result = client._delete_file(drive_id=folder_id.cloud_key)
        return result and True or False

    def _google_drive_upload_file(self, folder_id, attachment_id, cloud_key, args):
        """
        The method to upload file to clouds

        Args:
         * the same as for _call_api_method of clouds.client (cloud.base)
         * args should contain attach_name

        Methods:
         * urlsafe_b64decode of base64
         * _upload_file of Google Drive Api Client

        Returns:
         * dict of values to write in ir.attachment

        Extra info:
         * we do not check for uniqueness of attachment name, since Gogole Drive would do that for us
        """
        client = self._context.get("cclients", {}).get(self.id)
        content = base64.urlsafe_b64decode(attachment_id.datas)
        result = client._upload_file(
            folder=folder_id.cloud_key,
            file_name=args.get("attach_name"),
            mimetype=attachment_id.mimetype,
            content=content,
            file_size=len(content),
        )
        result = {
            "cloud_key": result.get("id"),
            "url": result.get("webViewLink"),
            "type": "url",
            "sync_cloud_folder_id": folder_id.id,
            "sync_client_id": self.id,
        }
        return result

    def _google_drive_update_file(self, folder_id, attachment_id, cloud_key, args):
        """
        Method to update file in clouds

        Args:
         * the same as for _call_api_method of clouds.client (cloud.base)
         * Args should contain attach_name

        Methods:
         * _move_or_update_file of Google Drive Api Client

        Returns:
         * dict to write in attachment

        Extra info:
         * we do not check for uniqueness of attachment name, since Gogole Drive would do that for us
        """
        client = self._context.get("cclients", {}).get(self.id)
        result = client._move_or_update_file(
            drive_id=attachment_id.cloud_key, new_parent=folder_id.cloud_key, new_name=args.get("attach_name"),
        )
        result = {
            "cloud_key": result.get("id"),
            "url": result.get("webViewLink"),
            "sync_cloud_folder_id": folder_id.id,
            "sync_client_id": self.id,
        }
        return result

    def _google_drive_delete_file(self, folder_id, attachment_id, cloud_key, args):
        """
        Method to delete file in clouds

        Args:
         * the same as for _call_api_method of clouds.client (cloud.base)

        Methods:
         * _delete_file of Google Drive Api Client

        Returns:
          * bool

        Extra info:
         * Actually the result of the operation is always an error. 204 if successful, so, return would never take place
        """
        result = False
        client = self._context.get("cclients", {}).get(self.id)
        result = client._delete_file(drive_id=attachment_id.cloud_key)
        return result and True or False

    def _google_drive_create_subfolder(self, folder_id, attachment_id, cloud_key, args):
        """
        The method to create clouds.folder in Odoo based on cloud client folder info

        Args:
         * the same as for _call_api_method of clouds.client (cloud.base)

        Methods:
         * _get_file_metadata of Google Drive Api Client

        Returns:
          * dict of clouds.folder values
        """
        client = self._context.get("cclients", {}).get(self.id)
        cdata = client._get_file_metadata(drive_id=cloud_key)
        result = {
            "cloud_key": cloud_key,
            "name": cdata.get("name"),
            "parent_id": folder_id.id,
            "own_client_id": self.id,
            "active": True,
            "url": cdata.get("webViewLink"),
        }
        return result

    def _google_drive_create_attachment(self, folder_id, attachment_id, cloud_key, args):
        """
        The method to create ir.attachment in Odoo based on cloud client file info

        Args:
         * the same as for _call_api_method of clouds.client (cloud.base)

        Methods:
         * _get_file_metadata of Google Drive Api Client

        Returns:
          * dict of ir.attachment values
        """
        client = self._context.get("cclients", {}).get(self.id)
        cdata = client._get_file_metadata(drive_id=cloud_key)
        result = {
            "cloud_key": cloud_key,
            "name": cdata.get("name"),
            "url": cdata.get("webViewLink"),
            "clouds_folder_id": folder_id.id,
            "sync_cloud_folder_id": folder_id.id,
            "sync_client_id": self.id,
            "type": "url",
            "mimetype": cdata.get("mimeType"),
        }
        return result

    def _google_drive_change_attachment(self, folder_id, attachment_id, cloud_key, args):
        """
        The method to write on ir.attachment in Odoo based on cloud client file info

        Args:
         * the same as for _call_api_method of clouds.client (cloud.base)

        Methods:
         * _get_file_metadata of Google Drive Api Client

        Returns:
          * dict of ir.attachment values
        """
        client = self._context.get("cclients", {}).get(self.id)
        cdata = client._get_file_metadata(drive_id=cloud_key)
        result = {"name": cdata.get("name"), "url": cdata.get("webViewLink")}
        return result

    def _google_drive_attachment_reverse(self, folder_id, attachment_id, cloud_key, args):
        """
        The method to create ir.attachment in Odoo based on cloud client file info

        Args:
         * the same as for _call_api_method of clouds.client (cloud.base)

        Methods:
         * _get_file_metadata of Google Drive Api Client
         * _download_file of Google Drive Api Client

        Returns:
          * dict of ir.attachment values

        Extra info:
         * IMPORTANT: mimetype should NOT be written here, since we already do that in backward sync creation.
           Otherwise, there might be conflicts
        """
        client = self._context.get("cclients", {}).get(self.id)
        cdata = client._get_file_metadata(drive_id=cloud_key)
        # IMPORTANT: do not write clouds_folder_id. It would break attachments moves
        result = {
            "cloud_key": False,
            "name": cdata.get("name"),
            "url": False,
            "type": "binary",
            "sync_cloud_folder_id": False,
            "sync_client_id": False,
        }
        binary_content = client._download_file(drive_id=cloud_key)
        result.update({"raw": binary_content})
        return result

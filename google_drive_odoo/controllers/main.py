# -*- coding: utf-8 -*-

import werkzeug

from odoo import _
from odoo.http import Controller, route, request


class google_drive_token(Controller):
    """
    Google drive controller to catch response from Google Drive API
    """
    @route("/google_drive_token", type="http", auth="user", website=False)
    def login_to_gdrive(self, **kwargs):
        """
        Method that handles incoming token from Google Drive

        Methods:
         * _return_specific_client_context of clouds.client
         * _generate_cloud_client_url of clouds.client
         * _gd_create_session of clouds.client
         * _gd_search_drive_id of clouds.client
         * _gd_root_folder_wrapper of clouds.client

        Returns:
         * related clouds view

        Extra info:
         * For the case not correct client is found (very rare case 2 gd clients are launched simultaneously),
           the method _gd_create_session would result in a credentials error
        """
        code = kwargs.get("code")
        ctx = request.env.context.copy()
        cloud_client_id = request.env["clouds.client"].search(
            [("state", "in", ["draft", "reconnect"]), ("method_key", "=", "google_drive")],
            order="last_establish DESC",
            limit=1,
        )
        if not cloud_client_id:
            return request.render("cloud_base.error_page", {"cloud_error": _("Client was not found")})
        cloud_url = cloud_client_id._generate_cloud_client_url()
        this_client_ctx = cloud_client_id._return_specific_client_context(True)
        if not this_client_ctx.get("cclients"):
            return werkzeug.utils.redirect(cloud_url)
        ctx.update(this_client_ctx)
        cloud_client_id = cloud_client_id.with_context(ctx)
        success, log_message = cloud_client_id._gd_create_session(code=code)
        if not success:
            cloud_client_id.error_state = log_message
            return werkzeug.utils.redirect(cloud_url)
        success, log_message = cloud_client_id._gd_search_drive_id()
        if not success:
            cloud_client_id.error_state = log_message
            return werkzeug.utils.redirect(cloud_url)
        success, log_message = cloud_client_id._gd_root_folder_wrapper()
        if not success:
            cloud_client_id.error_state = log_message
            return werkzeug.utils.redirect(cloud_url)
        cloud_client_id.error_state = False
        return werkzeug.utils.redirect(cloud_url)

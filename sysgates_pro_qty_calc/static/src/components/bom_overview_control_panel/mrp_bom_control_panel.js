/** @odoo-module **/
//console.log('Starting...');
import { patch } from "@web/core/utils/patch";
import { BomOverviewControlPanel } from "@mrp/components/bom_overview_control_panel/mrp_bom_overview_control_panel";


patch(BomOverviewControlPanel.prototype, {
    setup() {
        super.setup();
        this.props.tall = this.props.tall || 1;
        this.props.width = this.props.width || 1;
        this.props.height = this.props.height || 1;
        console.log('This: ', this);
    },
    updateQuantity(ev) {
        console.log("updateQuantity");
        const newVal = isNaN(ev.target.value) ? 1 : parseFloat(parseFloat(ev.target.value).toFixed(this.precision));
        this.props.changeBomQuantity(newVal);
    },
//    //////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
    async updateBomLines(){
        console.log("updateBomLines")
        let active_id = this.props.data.bom_id
        let tall = this.props.tall
        let width = this.props.width
        let height = this.props.height
        await this.env.services.orm.call("mrp.bom", "set_products_quantity_1", [active_id, tall, width, height]);
        super.setup();
        //        console.log("1: ", this.props.tall)
        //        this.props.changeBomQuantity(2);
        //        console.log("2: ", this.props.tall)
    },

    async updateTall(ev) {
        console.log("updateTall");
        const tallNewVal = isNaN(ev.target.value) ? 1 : parseFloat(parseFloat(ev.target.value).toFixed(this.precision));
        this.props.tall = tallNewVal;
        this.updateBomLines();
    },

    updateWidth(ev) {
        console.log("updateWidth");
        const widthNewVal = isNaN(ev.target.value) ? 1 : parseFloat(parseFloat(ev.target.value).toFixed(this.precision));
        this.props.tall = widthNewVal
    },

    updateHeight(ev) {
        console.log("updateHeight");
        const heightNewVal = isNaN(ev.target.value) ? 1 : parseFloat(parseFloat(ev.target.value).toFixed(this.precision));
        this.props.height = heightNewVal
    },

    onKeyPress(ev) {
        if (ev.key === "Enter") {
            ev.preventDefault();
            if (ev.target.id == 'bom_quantity'){
                this.updateQuantity(ev);
            } else if (ev.target.id === 'tall'){
                this.updateTall(ev);
            } else if (ev.target.id === 'width'){
                this.updateWidth(ev);
            } else if (ev.target.id === 'height'){
                this.updateHeight(ev);
            }
        }
    }

});

//BomOverviewControlPanel.props = {
//    ...BomOverviewControlPanel.props,
//    changeTall: Function,
//}
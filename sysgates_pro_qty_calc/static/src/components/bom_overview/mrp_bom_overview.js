/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { BomOverviewComponent } from "@mrp/components/bom_overview/mrp_bom_overview";


patch(BomOverviewComponent.prototype, {
    setup() {
        super.setup();
        console.log('This: ', this);
    },
    async onChangeTall(newTall) {
        console.log('newTall: ', newTall);
    },


});
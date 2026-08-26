import {Component, useState} from "@odoo/owl";
import {registry} from "@web/core/registry";
import {useService} from "@web/core/utils/hooks";

export class ReviewsTable extends Component {
    setup() {
        super.setup();
        this.orm = useService("orm");
        this.state = useState({
            collapse: false,
        });
    }

    _getReviewData() {
        const records = this.env.model.root.data.review_ids.records;
        const reviewData = records.map((record) => record.data);
        
        // // Debug logging
        // console.log("TierReview _getReviewData() - Number of records:", records.length);
        // reviewData.forEach((data, index) => {
        //     console.log(`Review ${index}:`, data);
            
        //     // Deep inspect the proxy objects
        //     if (data.requested_by) {
        //         console.log(`  requested_by type:`, typeof data.requested_by);
        //         console.log(`  requested_by properties:`, Object.getOwnPropertyNames(data.requested_by));
        //         console.log(`  requested_by.id:`, data.requested_by.id);
        //         console.log(`  requested_by.display_name:`, data.requested_by.display_name);
        //         console.log(`  requested_by.name:`, data.requested_by.name);
        //     }
            
        //     if (data.done_by) {
        //         console.log(`  done_by type:`, typeof data.done_by);
        //         console.log(`  done_by properties:`, Object.getOwnPropertyNames(data.done_by));
        //         console.log(`  done_by.id:`, data.done_by.id);
        //         console.log(`  done_by.display_name:`, data.done_by.display_name);
        //         console.log(`  done_by.name:`, data.done_by.name);
        //     }
        // });
        
        return reviewData;
    }

    onToggleCollapse(ev) {
        const panelHeading = ev.currentTarget.closest(".panel-heading");
        const collapseDiv = panelHeading.nextElementSibling.matches("div#collapse1")
            ? panelHeading.nextElementSibling
            : null;
        if (!collapseDiv) return;
        if (this.state.collapse) {
            collapseDiv.style.display = "none";
        } else {
            collapseDiv.style.display = "block";
        }
        this.state.collapse = !this.state.collapse;
    }
}

ReviewsTable.template = "base_tier_validation.Collapse";

export const reviewsTableComponent = {
    component: ReviewsTable,
    supportedTypes: ["one2many"],
    relatedFields: [
        {name: "id", type: "integer"},
        {name: "sequence", type: "integer"},
        {name: "name", type: "char"},
        {name: "display_status", type: "char"},
        {name: "todo_by", type: "char"},
        {name: "status", type: "char"},
        {name: "reviewed_formated_date", type: "char"},
        {name: "comment", type: "char"},
        {name: "requested_by", type: "many2one", relation: "res.users"},
        {name: "done_by", type: "many2one", relation: "res.users"},
    ],
};

registry.category("fields").add("form.tier_validation", reviewsTableComponent);

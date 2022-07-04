// Register event listeners
import {Tooltip} from "bootstrap";

/***
 * Initialize all global listeners
 * */
export function register_listeners() {
    boostrapTooltipActivation();
}

/***
 * Initialize bootstrap tooltip component.
 * https://getbootstrap.com/docs/5.0/components/tooltips/#example-enable-tooltips-everywhere
 */
function boostrapTooltipActivation() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new Tooltip(tooltipTriggerEl)
    })
}



// Register event listeners
import {Tooltip} from "bootstrap";

/***
 * Initialize all global listeners
 * */
export function register_listeners() {
    checkAllListener();
    boostrapTooltipActivation();
}

/***
 * Adds a click event listener to a checkbox with id #check-all.
 * When the event listener is triggered, changes the state of all checkboxes
 * on the page to the same state, as the #check-all checkbox.
 */
function checkAllListener() {
    const check_all = document.getElementById('check-all') as HTMLInputElement;
    check_all?.addEventListener("click", function (event) {
        /**
         * find all checkboxes in current dashboard and toggle checked all / none
         */
        const inputs = document.querySelectorAll("input[type='checkbox']") as NodeListOf<HTMLInputElement>;
        if (this.checked) {
            for (let minput of inputs) {
                minput.checked = true;
            }
        } else {
            for (let minput of inputs) {
                minput.checked = false;
            }
        }
    });
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



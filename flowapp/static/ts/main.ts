import {Modal, Tooltip} from 'bootstrap';

// Register event listeners
const check_all = document.getElementById('check-all') as HTMLInputElement;
check_all?.addEventListener("click", function(event){
    /**
     * find all checkboxes in current dashboard and toggle checked all / none
     */
    const inputs = document.querySelectorAll("input[type='checkbox']") as NodeListOf<HTMLInputElement>;
    if (this.checked) {
        for(let minput of inputs) {
            minput.checked = true;
        }
    } else {
        for(let minput of inputs) {
            minput.checked = false;
        }
    }
});

// Specify functions

function fillOrganization(ipInputId: string, maskInputId: string) {
    const modalContainer = document.getElementById('orgSelectModal');
    if (!modalContainer) {
        return;
    }
    const modal = new Modal(modalContainer, {backdrop: true});
    modal.show();
}
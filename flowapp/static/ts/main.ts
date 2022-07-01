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

const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
  return new Tooltip(tooltipTriggerEl)
})

// Specify functions

export function fillOrganization(ipInputId: string, maskInputId: string): void {
    const modalContainer = document.getElementById('orgSelectModal');
    if (!modalContainer) {
        return;
    }
    const modal = new Modal(modalContainer, {backdrop: true});
    modal.show();
    const btn = document.getElementById('fill-org-btn');
    if (btn) {
        btn.onclick = function () {
            fillOrgValue(document.getElementById(ipInputId) as HTMLInputElement,
                document.getElementById(maskInputId) as HTMLInputElement);
            modal.hide();
        }
    }
}

 export function fillOrgValue(ipField: HTMLInputElement | null, maskField: HTMLInputElement | null) {
    const org_select = document.getElementById('orgSelect') as HTMLInputElement;
    if (!org_select) {
        return;
    }
    const val = org_select.value.split('/');
    if (ipField) {
        ipField.value = val[0];
    }
    if (maskField) {
        maskField.value = val[1];
    }
}
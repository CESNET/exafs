import {Modal} from "bootstrap";

/***
 * Show a bootstrap modal window identified by css ID #orgSelectModal.
 * The modal is specified as a jinja macro "fill_org_form" in the
 * flowapp/templates/forms/macros.j2 file.
 *
 * Calling this function opens the modal and registers a callback to
 * its "Use range" button. The callback reads the value from the
 * range selection input and applies it to appropriate input fields.
 *
 * @param {string} ipInputId   - id of the input field,
 *                               where organization IP address should be filled to
 * @param {string} maskInputId - id of the input field,
 *                               where organization IP mask should be filled to
 */
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
            fillOrgValue(
                document.getElementById(ipInputId) as HTMLInputElement,
                document.getElementById(maskInputId) as HTMLInputElement
            );
            modal.hide();
        }
    }
}

/***
 * Fill value from the
 */
function fillOrgValue(ipField: HTMLInputElement | null, maskField: HTMLInputElement | null) {
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

/***
 * This function can be called as a keypress event listener on
 * any text input. Listens to all key presses and if the key value is
 * equal to the key parameter, the focus is switched to an input field
 * identified by the focusID parameter. The target key is not inputted to the
 * original field nor the target field.
 *
 * @param {KeyboardEvent}   event   - Event that triggered this function
 * @param {string}          key     - Keypress to listen to, should be the key name (uses event.key)
 * @param {string}          focusId - ID of the target input, that receives focus after the key is pressed
 */
export function switchFocusOnKeypress(event: KeyboardEvent, key: string, focusId: string) {
    if (event.key == key) {
        event.preventDefault();
        const focus = document.getElementById(focusId) as HTMLInputElement;
        if (focus) {
            focus.focus();
        }
    }
}
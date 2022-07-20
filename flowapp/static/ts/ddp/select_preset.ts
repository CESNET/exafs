import {
    AVAILABLE_PRESET_FIELDS,
    DDPPreset,
    DDPPresetField,
    DDPRuleType,
    getPresetField,
    PresetFieldType,
    RangePresetFieldOpts,
    SliderType
} from "./ddp_presets";
import {createPresetFormField} from "./inputs";
import {attachHtmlToRef, clearAllChildren, createChild, removeElement, stringToHtml} from "../renderer";
import {logarithmicValueFromPos} from "./logscale";

let ddpPreset: DDPPreset;


export function initSelectPresetForm(preset: DDPPreset, parentId: string, moreOptsToggleId: string, initData?: { [key: string]: any }) {
    const ruleTypePresetField: DDPPresetField =
        {
            defaultValue: preset.fields.rule_type,
            name: "rule_type",
            printName: "Rule type",
            type: PresetFieldType.TEXT,
            rule_types: [DDPRuleType.AMPLIFICATION, DDPRuleType.FILTER, DDPRuleType.SYN_DROP, DDPRuleType.TCP_AUTHENTICATOR]
        };
    ddpPreset = preset;
    const ruleTypeFieldHtml = createPresetFormField(ruleTypePresetField, 0, preset.fields.rule_type, true);
    let fields = wrapField(ruleTypeFieldHtml, 0, ruleTypePresetField.printName);
    let id = 1;
    Object.entries(preset.fields).forEach(([key, value], index) => {
        if (key !== 'rule_type') {
            let field = {...getPresetField(key)} as DDPPresetField;
            if (initData && 'ddp_' + key in initData) {
                value = initData['ddp_' + key] as any;
            }
            const fieldHtml = createPresetFormField(field, id, value, !isEditable(key, preset.editable));
            fields += '\n' + wrapField(fieldHtml, id, field.printName);
            id++;
        }
    });
    fields += '<hr class="my-2>';
    clearAllChildren(parentId);
    createChild(fields, parentId);

    const toggleMoreOpts = document.getElementById(moreOptsToggleId);
    toggleMoreOpts?.classList.remove('d-none');
}

export function changeAdvancedOptionsText(advancedOptsId: string, isOpen: boolean) {
    const elem = document.getElementById(advancedOptsId);
    if (elem) {
        elem.innerHTML = isOpen ? 'Hide advanced options <i class="bi bi-caret-up-fill"></i>'
            : 'Show advanced options <i class="bi bi-caret-down-fill"></i>';
    }
}


/***
 * Recalculate the range sliders using logarithmic scales and
 * set low/high values. Form data can not be directly changed,
 * therefore new hidden field with the same name as the range
 * slider is added for each slider, containing the correct value.
 * Removes the original sliders, so this function should be called
 * as an event listener to onSubmit event (or as close to submitting as possible).
 *
 * @param {HTMLFormElement} formRef - Form element containing range sliders.
 *
 * @param {string} destIpId - CSS ID of the IP address input
 * @param {string} protocolId - CSS ID of the protocol input
 * @returns {boolean} - True if the form is valid, false otherwise.
 * */
export function beforeIPFormSend(formRef: HTMLFormElement, destIpId: string, protocolId: string) {
    const data = new FormData(formRef);
    if (data.get('action') !== '4') {
        return true;
    }
    const rangeFields = getAllRangeFields();
    for (const f of rangeFields) {
        const value = data.get('ddp_' + f.name);
        if (value !== null) {
            const opts = f.options as RangePresetFieldOpts;
            const originalElem = document.querySelector(`[name="${'ddp_' + f.name}"]`) as HTMLElement;
            if (originalElem) {
                removeElement(originalElem);
            }
            if (opts.type === SliderType.LOGARITHMIC) {
                const input =
                    `<input type="hidden" value="${logarithmicValueFromPos(+value, opts.low, opts.high)}" name="${'ddp_' + f.name}">`;
                attachHtmlToRef(stringToHtml(input), formRef);
            } else {
                const input =
                    `<input type="hidden" value="${value}" name="${'ddp_' + f.name}">`;
                attachHtmlToRef(stringToHtml(input), formRef);
            }
        }
    }
    return true;
}

function wrapField(fieldHtml: string, id: number, label: string) {
    return `<div class="row"><div class="my-3 col-md-6 col-sm-12 px-3">
<label for="presetInput${id}" class="form-label">${label}</label>
${fieldHtml}
<p class="form-text text-danger" id="form-error-msg${id}"></p>
</div></div>`
}

function isEditable(key: string, editables: string[]) {
    return editables.includes(key);
}

function getAllRangeFields(): DDPPresetField[] {
    return AVAILABLE_PRESET_FIELDS.filter((preset) => {
        return preset.type === PresetFieldType.RANGE
    });
}

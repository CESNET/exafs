import {
    DDPPreset,
    DDPPresetField,
    DDPRuleType,
    EnumPresetFieldOpts,
    getPresetField,
    getPresetFieldsByRuleType,
    PresetFieldType,
    RangePresetFieldOpts
} from "./ddp_presets";
import {attachHtmlTo, stringToHtml} from "../renderer";
import {formatSIUnitNumber} from "../utils";
import {logarithmicValueFromPos, posFromLogarithmicValue} from "./logscale";
import {sendToBackend} from "../http";

let presetFormContext = {
    maxId: 0,
    selectedRuleType: DDPRuleType.FILTER,
    activeFields: [] as DDPPresetField[]
}

export function initEditPresetsForm(preset: DDPPreset, containerId: string, ruleTypeSelectId: string) {
    const ruleTypeSelect = document.getElementById(ruleTypeSelectId) as HTMLInputElement;
    if (ruleTypeSelect) {
        ruleTypeSelect.value = preset.fields.rule_type as string;
    }
    presetFormContext.selectedRuleType = preset.fields.rule_type as DDPRuleType;
    Object.entries(preset.fields).forEach(([key, value], index) => {
        if (key !== 'rule_type') {
            const id = presetFormAddField(containerId, preset.fields.rule_type, key, value);
            if (id !== -1) {
                const check = document.getElementById(`userEditable${id}`) as HTMLInputElement;
                check.checked = preset.editable.includes(key);
            }
        }
    });
}

export function presetFormAddField(containerId: string, ruleType: DDPRuleType | string, initFieldName: string, initValue?: any): number {
    presetFormContext.selectedRuleType = ruleType as DDPRuleType;
    // Create a copy instead of passing a reference
    let field = {...getPresetField(initFieldName)} as DDPPresetField;
    if (field) {
        let form = createCommonWrapper(createPresetFormField(field, presetFormContext.maxId, initValue), presetFormContext.maxId, initFieldName)
        field.formId = presetFormContext.maxId;
        presetFormContext.activeFields.push(field);
        presetFormContext.maxId++;
        attachHtmlTo(stringToHtml(form), containerId);
        checkForDuplicates(field.formId, initFieldName);
        return field.formId;
    }
    return -1;
}

export function updatePresetFormField(keySelect: HTMLSelectElement, id: number) {
    // Create a copy instead of passing a reference
    const idx = getFieldIndexById(id);
    const prevName = presetFormContext.activeFields[idx].name;
    const field = {...getPresetField(keySelect.value)} as DDPPresetField;
    const container = document.getElementById(`fieldValueContainer${id}`);
    removeInvalidSelectOptions(keySelect, id);
    clearInvalidDuplicateWarnings(id, prevName);
    if (field) {
        field.formId = id;
        if (container) {
            container.innerHTML = createPresetFormField(field, id);
        }
        if (idx !== -1) {
            presetFormContext.activeFields[idx] = field;
        }
        checkForDuplicates(id, keySelect.value);
    } else if (container) {
        container.innerHTML = '<p class="text-danger">Invalid rule field name!</p>';
    }
}


export function removeField(id: number) {
    const container = document.getElementById(`fieldContainer${id}`);
    if (container) {
        container.parentElement?.removeChild(container);
        const index = presetFormContext.activeFields.findIndex(p => p.formId === id);
        if (index !== -1) {
            // Remove duplicate field warning if the only duplicate is removed
            clearInvalidDuplicateWarnings(id, presetFormContext.activeFields[index].name)
            presetFormContext.activeFields.splice(index, 1);
        }
    }
}

export function rebuildDropdowns(ruleType: DDPRuleType) {
    const fieldCache = getPresetFieldsByRuleType(ruleType);
    for (let i = 0; i < presetFormContext.maxId; i++) {
        const field = document.getElementById('fieldSelect' + i) as HTMLSelectElement;
        if (field) {
            field.classList.remove('is-invalid');
            let wrongOpt = '';
            if (!fieldExistsInCache(fieldCache, field)) {
                wrongOpt = `<option value=${field.value} selected invalid>${field.options[field.selectedIndex].text}</option>`;
                field.classList.add('is-invalid');
                setErrorMessage(i, 'Invalid field for selected rule type');
            } else {
                setErrorMessage(i, '');
            }
            field.innerHTML = createFieldSelectionDropdownOptions(ruleType, field.value, fieldCache) + wrongOpt;
        }
    }
}

export function onPresetNameChange(elem: HTMLInputElement, errorMessageId: string) {
    const msg = document.getElementById(errorMessageId);
    if (elem.value !== '') {
        if (msg) {
            msg.innerText = '';
        }
        elem.classList.remove('is-invalid');
    } else {
        if (msg) {
            msg.innerText = 'Preset name is required';
        }
        elem.classList.add('is-invalid');
    }
}

export function savePreset(presetNameInputId: string,
                           ruleType: DDPRuleType,
                           csrf_token: string,
                           callbackUrl: string,
                           saveBtnId: string,
                           successRedirectUrl: string) {
    if (formHasErrors()) {
        alert('Preset has errors! Fix them before saving.');
        return;
    }
    let data = new FormData;
    let editable = '';
    const presetName = getPresetName(presetNameInputId);
    const btn = document.getElementById(saveBtnId);
    if (!presetName) {
        return
    }
    data.append('name', presetName);
    data.append('rule_type', ruleType.toString());
    data.append('csrf_token', csrf_token);
    for (let field of presetFormContext.activeFields) {
        const currentField = document.getElementById(`presetInput${field.formId}`);
        const currentKey = document.getElementById(`fieldSelect${field.formId}`) as HTMLSelectElement;
        const userEditable = document.getElementById(`userEditable${field.formId}`) as HTMLInputElement;
        if (currentField && currentKey && userEditable) {
            if (userEditable.checked) {
                editable += currentKey.value + ';';
            }
            if (currentField.hasChildNodes() && currentField.tagName.toLowerCase() !== 'select') {
                data.append(currentKey.value, checkboxesToStr(currentField));
            } else {
                let c = currentField as HTMLInputElement;
                if (field.type === PresetFieldType.RANGE && field.options) {
                    const val = logarithmicValueFromPos(c.valueAsNumber, (field.options as RangePresetFieldOpts).low, (field.options as RangePresetFieldOpts).high)
                    data.append(currentKey.value, val.toString());
                } else {
                    data.append(currentKey.value, c.value.toString());
                }
            }
        }
    }
    data.append('editable', editable);
    let originalBtnContent = '';
    if (btn) {
        originalBtnContent = btn.innerHTML;
        btn.setAttribute('disabled', '');
        btn.innerHTML = `<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
  Saving...`;
    }

    sendToBackend(data, callbackUrl, "POST",
        (response: Response) => {
            if (btn) {
                btn.innerHTML = 'Saved';
                btn.removeAttribute('disabled');
            }
            window.location.href = successRedirectUrl;

        }, (error: string) => {
            console.log(error)
            if (btn) {
                btn.innerHTML = originalBtnContent;
                btn.removeAttribute('disabled');
            }
            alert('Could not save preset: ' + error);
        });
}

function getPresetName(presetNameInputId: string): string | null {

    const presetNameInput = document.getElementById(presetNameInputId) as HTMLInputElement;
    if (!presetNameInput) {
        alert('Wrong preset name input ID supplied to savePreset()!');
        return null;
    }
    if (!presetNameInput.value) {
        window.scrollTo({ top: 0, behavior: 'smooth' });
        presetNameInput.classList.add('is-invalid');
        presetNameInput.focus();
        const presetNameError = document.getElementById('presetNameError');
        if (presetNameError) {
            presetNameError.innerText = 'Preset name is required.';
        }
        return null;
    }
    return presetNameInput.value;
}

function checkboxesToStr(parent: HTMLElement): string {
    let val = '';
    for (let child of parent.children) {
        for (let grandchild of child.children) {
            if (grandchild.tagName.toLowerCase() === 'input' && grandchild.getAttribute('type') === 'checkbox') {
                const c = grandchild as HTMLInputElement
                if (c.checked) {
                    val += c.value + ','
                }
            }
        }
    }
    return val;
}

function createRangePresetFormField(field: DDPPresetField, id: number, initValue?: number) {
    const opts = field.options as RangePresetFieldOpts;
    if (!initValue) {
        initValue = 50
    } else {
        initValue = posFromLogarithmicValue(initValue, opts.low, opts.high);
    }
    return `
<div class="row form-text">
<div class="col-4">Restrictive</div>
<div class="col-4 text-center" id="rangeVal${id}">${formatSIUnitNumber(logarithmicValueFromPos(initValue, opts.low, opts.high), 2, opts.unit)}</div>
<div class="col-4 text-end">Permissive</div>
</div>
<input class="form-range" type="range" value="${initValue}" id="presetInput${id}" min=0 max=100 step=1
onChange="ExaFS.updateRangeValText(this, 'rangeVal${id}', ${opts.low}, ${opts.high}, '${opts.unit}')"
onInput="ExaFS.updateRangeValText(this, 'rangeVal${id}', ${opts.low}, ${opts.high}, '${opts.unit}')">`;
}

function creteBoolPresetFormField(initValue: any, id: number) {
    return `<div class="form-check form-switch">
<input class="form-check-input" type="checkbox" value="${initValue}" id="presetInput${id}"></div>`;
}

function creteEnumPresetFormField(field: DDPPresetField, initValue: any, id: number) {
    let opts = field.options as EnumPresetFieldOpts;
    let values = '';

    if (opts.multi) {
        const selected = (initValue as string).split(',');
        for (const val of opts.values) {
            values += `<div class="form-check form-check-inline">
                      <input class="form-check-input" 
                          type="checkbox" 
                          id="${val}Check${id}" 
                          value="${val}"
                          ${selected.includes(val as string) ? 'checked="checked"' : ''}>
                      <label class="form-check-label" for="${val}Check${id}">${val}</label>
                    </div>`;
        }
        return `<div class="form-check form-check-inline" id="presetInput${id}">${values}</div>`;
    } else {
        for (const val of opts.values) {
            values += `<option value=${val} ${val === initValue ? 'selected' : ''}>${val}</option>`
        }
        return `<select class="form-select" id="presetInput${id}">${values}</select>`;
    }
}

function createPresetFormField(field: DDPPresetField, id: number, initValue?: any): string {
    let val = '<div class="fade-in-fwd">';
    if (!initValue) {
        initValue = field.defaultValue;
    }
    switch (field.type) {
        case PresetFieldType.TEXT:
            val += `<input class="form-control" type="text" value="${initValue}" id="presetInput${id}">`;
            break;
        case PresetFieldType.NUMBER:
            val += `<input class="form-control" type="number" value="${initValue}" id="presetInput${id}">`;
            break;
        case PresetFieldType.RANGE:
            val += createRangePresetFormField(field, id, initValue);
            break;
        case PresetFieldType.BOOL:
            val += creteBoolPresetFormField(initValue, id);
            break;
        case PresetFieldType.ENUM:
            val += creteEnumPresetFormField(field, initValue, id);
            break;
    }
    if (field.description) {
        val += `<div class="form-text">${field.description}</div></div>`
    }
    return val;
}

function createCommonWrapper(elem: string, id: number, initKey?: string): string {
    return `<div id="fieldContainer${id}">
<hr class="d-md-none my-2">
<div class="row my-3 fade-in-fwd">
    <div class="col-sm-12 col-md-4 my-1">
    <select class="form-select" id="fieldSelect${id}" onChange="ExaFS.updatePresetFormField(this, ${id})">
        ${createFieldSelectionDropdownOptions(presetFormContext.selectedRuleType, initKey)}
</select>
<p class="form-text text-danger" id="form-error-msg${id}"></p>
</div>
<div class="col-sm-12 col-md-4 my-1" id="fieldValueContainer${id}">
    ${elem}
</div>
<div class="col-sm-12 col-md-4 my-1">
<div class="form-check form-switch form-check-inline">
  <input class="form-check-input" type="checkbox" id="userEditable${id}">
  <label class="form-check-label" for="userEditable${id}">User can edit</label>
</div>
<button class="btn btn-outline-danger mx-2" role="button" onclick="ExaFS.removeField(${id})" title="Remove line"><i class="bi bi-x-lg"></i></button>
</div>
</div>
</div>`;
}

function createFieldSelectionDropdownOptions(ruleType: DDPRuleType, selected?: string, availableFields?: DDPPresetField[]): string {
    let retval = '';
    if (!availableFields) {
        availableFields = getPresetFieldsByRuleType(ruleType);
    }
    for (const f of availableFields) {
        retval += `<option value="${f.name}" ${f.name === selected ? 'selected' : ''}>${f.printName}</option>`;
    }
    return retval;
}

function fieldExistsInCache(fieldCache: DDPPresetField[], field: HTMLSelectElement): boolean {
    return !!fieldCache.find((f) => {
        return f.name === field.value
    });
}

function setErrorMessage(id: number, message: string) {
    const errorElem = document.getElementById('form-error-msg' + id);
    if (errorElem) {
        errorElem.innerText = message;
    }
}

/***
 * Returns index from the activeFields array from presetFormContext by
 * form ID. Returns -1 if given ID is not in activeFields.
 * */
function getFieldIndexById(id: number): number {
    return presetFormContext.activeFields.findIndex((field) => {
        return field.formId === id;
    })
}

function removeInvalidSelectOptions(select: HTMLSelectElement, id: number) {
    let children = select.children;
    for (let i = 0; i < children.length; i++) {
        if (children[i].hasAttribute('invalid')) {
            select.removeChild(children[i]);
        }
    }
    setErrorMessage(id, '');
    select.classList.remove('is-invalid');
}

function findDuplicateKeys(sourceId: number, name: string): DDPPresetField[] {
    return presetFormContext.activeFields.filter((field) => {
        return field.name === name && field.formId !== sourceId;
    });
}

function setFieldAsDuplicate(id: number) {
    const field = document.getElementById('fieldSelect' + id);
    field?.classList.add('is-invalid');
    setErrorMessage(id, 'Duplicate rule field');
}

function clearInvalidDuplicateWarnings(id: number, name: string) {
    const duplicates = findDuplicateKeys(id, name);
    if (duplicates.length === 1 && duplicates[0].formId !== undefined) {
        const select = document.getElementById('fieldSelect' + duplicates[0].formId);
        select?.classList.remove('is-invalid');
        setErrorMessage(duplicates[0].formId, '');
    }
}

function checkForDuplicates(id: number, name: string) {
    const duplicates = findDuplicateKeys(id, name);
    if (duplicates.length > 0) {
        for (const d of duplicates) {
            if (d.formId !== undefined) {
                setFieldAsDuplicate(d.formId);
            }
        }
        setFieldAsDuplicate(id);
    }
}

function formHasErrors(): boolean {
    const errorFields = document.querySelectorAll('.is-invalid');
    return errorFields.length > 0;
}
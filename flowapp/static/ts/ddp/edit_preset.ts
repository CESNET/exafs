import {
    DDPPreset,
    DDPPresetField,
    DDPRuleType,
    getPresetField,
    getPresetFieldsByRuleType,
    PresetFieldRequirementRelationship,
    PresetFieldType,
    RangePresetFieldOpts,
    SliderType
} from "./ddp_presets";
import {createChild} from "../renderer";
import {logarithmicValueFromPos} from "./logscale";
import {sendFormDataToBackend} from "../http";
import {checkboxesToStr, createPresetFormField} from "./inputs";

let presetFormContext = {
    maxId: 0,
    selectedRuleType: DDPRuleType.FILTER,
    activeFields: [] as DDPPresetField[]
}
let changes = false;

export function addBeforeUnloadEventListener() {
    window.addEventListener("beforeunload", function (e) {
        let confirmationMessage = 'There are unsaved changes in the rule template, are you sure you want to exit before saving?';
        if (!changes) {
            return undefined;
        }
        (e || window.event).returnValue = confirmationMessage; //Gecko + IE
        return confirmationMessage; //Gecko + Webkit, Safari, Chrome etc.
    });
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
    checkFieldRequirements(presetFormContext.activeFields, presetFormContext.selectedRuleType);
}

export function presetFormAddField(containerId: string, ruleType: DDPRuleType | string, initFieldName: string, initValue?: any): number {
    presetFormContext.selectedRuleType = ruleType as DDPRuleType;
    // Create a copy instead of passing a reference
    let field = {...getPresetField(initFieldName)} as DDPPresetField;
    if (field) {
        changes = true;
        let form = createCommonWrapper(createPresetFormField(field, presetFormContext.maxId, initValue), presetFormContext.maxId, initFieldName)
        field.formId = presetFormContext.maxId;
        presetFormContext.activeFields.push(field);
        presetFormContext.maxId++;
        createChild(form, containerId);
        checkForDuplicates(field.formId, initFieldName);
        return field.formId;
    }
    return -1;
}

export function updatePresetFormField(keySelect: HTMLSelectElement, id: number) {
    const idx = getFieldIndexById(id);
    const prevName = presetFormContext.activeFields[idx].name;
    // Create a copy instead of passing a reference
    const field = {...getPresetField(keySelect.value)} as DDPPresetField;
    const container = document.getElementById(`fieldValueContainer${id}`);
    removeInvalidSelectOptions(keySelect, id);
    clearInvalidDuplicateWarnings(id, prevName);
    // checkRequirements(keySelect.value)
    if (field) {
        changes = true;
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
        changes = true;
        container.parentElement?.removeChild(container);
        const index = presetFormContext.activeFields.findIndex(p => p.formId === id);
        if (index !== -1) {
            // Remove duplicate field warning if the only duplicate is removed
            clearInvalidDuplicateWarnings(id, presetFormContext.activeFields[index].name)
            presetFormContext.activeFields.splice(index, 1);
        }
    }
}

export function onRuleTypeChange(ruleType: DDPRuleType) {
    const fieldCache = getPresetFieldsByRuleType(ruleType);
    for (let i = 0; i < presetFormContext.maxId; i++) {
        const field = document.getElementById('fieldSelect' + i) as HTMLSelectElement;
        if (field) {
            field.classList.remove('is-invalid');
            let wrongOpt = '';
            if (!fieldExistsInCache(fieldCache, field)) {
                wrongOpt = `<option value=${field.value} selected invalid>${field.options[field.selectedIndex].text}</option>`;
                field.classList.add('is-invalid');
                setKeyErrorMessage(i, 'Invalid field for selected rule type');
            } else {
                setKeyErrorMessage(i, '');
            }
            field.innerHTML = createFieldSelectionDropdownOptions(ruleType, field.value, fieldCache) + wrongOpt;
        }
    }
}

export function onPresetNameChange(elem: HTMLInputElement, errorMessageId: string) {
    const msg = document.getElementById(errorMessageId);
    changes = true;
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
    checkFieldRequirements(presetFormContext.activeFields, presetFormContext.selectedRuleType);
    if (formHasErrors()) {
        alert('Preset has errors! Fix them before saving.');
        return;
    }
    changes = false;
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
                    const opts = field.options as RangePresetFieldOpts;
                    let val = c.valueAsNumber;
                    if (opts.type === SliderType.LOGARITHMIC) {
                        val = logarithmicValueFromPos(c.valueAsNumber, opts.low, opts.high)
                    }
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

    sendFormDataToBackend(data, callbackUrl, "POST")
        .then(
            (response: Response) => {
                if (response.status == 200 || response.status == 201) {
                    if (btn) {
                        btn.innerHTML = 'Saved';
                        btn.removeAttribute('disabled');
                    }
                    window.location.href = successRedirectUrl;
                } else {
                    response.text().then(text => {
                        alert('Server returned error status ' + response.status + '. Check the console for more details');
                        console.error(text);
                        if (btn) {
                            btn.innerHTML = 'Errored';
                            btn.removeAttribute('disabled');
                        }
                    });
                }
            })
        .catch((error: string) => {
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
        window.scrollTo({top: 0, behavior: 'smooth'});
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
    setKeyErrorMessage(id, '');
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
    setKeyErrorMessage(id, 'Duplicate rule field');
}

function clearInvalidDuplicateWarnings(id: number, name: string) {
    const duplicates = findDuplicateKeys(id, name);
    if (duplicates.length === 1 && duplicates[0].formId !== undefined) {
        const select = document.getElementById('fieldSelect' + duplicates[0].formId);
        select?.classList.remove('is-invalid');
        setKeyErrorMessage(duplicates[0].formId, '');
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

function setKeyErrorMessage(id: number, message: string) {
    const errorElem = document.getElementById('form-error-msg' + id);
    const selectElem = document.getElementById('fieldSelect' + id)
    if (errorElem && selectElem) {
        errorElem.innerText = message;
        if (message == '') {
            selectElem.classList.remove('is-invalid');
        } else {
            selectElem.classList.add('is-invalid');
        }
    }
}


function checkFieldRequirements(fields: DDPPresetField[], rule_type: DDPRuleType) {
    console.log('Checking field requirements');
    for (const f of fields) {
        if (f.requires_fields && f.formId !== undefined) {
            const reqs = findUnsatisfiedRequirements(f, fields, rule_type);
            console.log(reqs);
            if (reqs.length !== 0) {
                let msg = '';
                for (let r of reqs) {
                    msg += ', ' + r;
                }
                msg = msg.slice(2)
                setKeyErrorMessage(f.formId, "Requirements not satisfied: " + msg)
            } else {
                setKeyErrorMessage(f.formId, '');
            }
        }
    }
}


function findUnsatisfiedRequirements(checkedField: DDPPresetField, allFields: DDPPresetField[], rule_type: DDPRuleType) {
    let notSatisfied: string[] = []
    const field = document.getElementById('presetInput' + checkedField?.formId) as HTMLInputElement;
    if (checkedField.requires_fields) {
        for (const r of checkedField.requires_fields) {
            if (r.rule_types.includes((rule_type))) {
                const idx = allFields.findIndex((field) => {
                    return field.name == r.name;
                });
                if (idx == -1 && r.relationship != PresetFieldRequirementRelationship.IsNotSet) {
                    notSatisfied.push(r.name + ' has to be set');
                } else {
                    const val = document.getElementById('presetInput' + allFields[idx].formId) as HTMLInputElement;
                    if (val && field) {
                        const value = val.value;
                        switch (r.relationship) {
                            case PresetFieldRequirementRelationship.IsNotSet:
                                notSatisfied.push(r.name + ' can not be set with this field');
                                break;
                            case PresetFieldRequirementRelationship.IsGreater:
                                if (value <= field.value) {
                                    notSatisfied.push(r.name + ' has to be greater than this field');
                                }
                                break;
                            case PresetFieldRequirementRelationship.IsLower:
                                if (value >= field.value) {
                                    notSatisfied.push(r.name + ' has to be lower than this field');
                                }
                                break;
                            case PresetFieldRequirementRelationship.IsGreaterOrEqual:
                                if (value < field.value) {
                                    notSatisfied.push(r.name + ' has to be greater or equal to this field');
                                }
                                break;
                            case PresetFieldRequirementRelationship.IsLowerOrEqual:
                                if (value > field.value) {
                                    notSatisfied.push(r.name + ' has to be lower or equal to this field');
                                }
                                break;
                            case PresetFieldRequirementRelationship.IsEqual:
                                if (value != field.value) {
                                    notSatisfied.push(r.name + ' has to be equal to this field');
                                }
                                break;
                            case PresetFieldRequirementRelationship.IsNotEqual:
                                if (value == field.value) {
                                    notSatisfied.push(r.name + ' has to be different from this field');
                                }
                                break;
                        }
                    }
                }
            }
        }
    }
    return notSatisfied;
}



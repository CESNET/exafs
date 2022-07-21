import {DDPPresetField, EnumPresetFieldOpts, PresetFieldType, RangePresetFieldOpts, SliderType} from "./ddp_presets";
import {logarithmicValueFromPos, posFromLogarithmicValue} from "./logscale";
import {formatSIUnitNumber} from "../utils";
import {validateField} from "./validators";

export function creteBoolPresetFormField(initValue: any, id: number, disabled: boolean = false) {
    return `<div class="form-check form-switch">
<input class="form-check-input" type="checkbox" value="${initValue}" id="presetInput${id}" ${boolToDisabledAttr(disabled)}></div>`;
}

export function createRangePresetFormField(field: DDPPresetField, id: number, initValue?: number, disabled: boolean = false) {
    const opts = field.options as RangePresetFieldOpts;
    if (initValue === undefined) {
        initValue = 50
    } else {
        if (opts.type === SliderType.LOGARITHMIC) {
            initValue = posFromLogarithmicValue(initValue, opts.low, opts.high);
        }
    }
    let initLabel = '';
    let minMaxStr = '';
    switch (opts.type) {
        case SliderType.LINEAR:
            initLabel = formatSIUnitNumber(initValue, 2, opts.unit);
            minMaxStr = `min=${opts.low} max=${opts.high}`;
            break;
        case SliderType.LOGARITHMIC:
            initLabel = formatSIUnitNumber(logarithmicValueFromPos(initValue, opts.low, opts.high), 2, opts.unit)
            minMaxStr = "min=0 max=100";
            break;
    }
    return `
<div class="row form-text">
<div class="col-4">Restrictive</div>
<div class="col-4 text-center" id="rangeVal${id}">${initLabel}</div>
<div class="col-4 text-end">Permissive</div>
</div>
<input class="form-range" type="range" value="${initValue}" id="presetInput${id}" ${minMaxStr} step=1 ${boolToDisabledAttr(disabled)}
onChange="ExaFS.updateRangeValText(this, ${id}, ${opts.low}, ${opts.high}, ${opts.type}, '${opts.unit}')" name="ddp_${field.name}"
onInput="ExaFS.updateRangeValText(this, ${id}, ${opts.low}, ${opts.high}, ${opts.type}, '${opts.unit}')">`;
}

export function creteEnumPresetFormField(field: DDPPresetField, id: number, initValue?: string, disabled: boolean = false) {
    let opts = field.options as EnumPresetFieldOpts;
    let values = '';

    if (opts.multi) {
        const selected = initValue?.split(',');
        for (const val of opts.values) {
            values += `<div class="form-check form-check-inline">
                      <input class="form-check-input" 
                          type="checkbox" 
                          name="ddp_${field.name}"
                          id="${val}Check${id}" 
                          value="${val}"
                          ${boolToDisabledAttr(disabled)}
                          ${selected?.includes(val as string) ? 'checked="checked"' : ''}>
                      <label class="form-check-label" for="${val}Check${id}">${val}</label>
                    </div>`;
        }
        return `<div class="form-check form-check-inline" id="presetInput${id}">${values}</div>`;
    } else {
        for (const val of opts.values) {
            values += `<option value=${val} ${val === initValue ? 'selected' : ''}>${val}</option>`
        }
        return `<select class="form-select" id="presetInput${id}" ${boolToDisabledAttr(disabled)} name="ddp_${field.name}">${values}</select>`;
    }
}

export function checkboxesToStr(parent: HTMLElement): string {
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

export function createPresetFormField(field: DDPPresetField, id: number, initValue?: any, disabled: boolean = false): string {
    let val = '<div class="fade-in-fwd">';
    if (initValue === undefined) {
        initValue = field.defaultValue;
    }
    const validator = field.validators ? `onInput="ExaFS.validateField('${field.name}', this, ${id})"` : '';
    switch (field.type) {
        case PresetFieldType.TEXT:
            val += `<input class="form-control" ${validator} name="ddp_${field.name}" type="text" value="${initValue}" id="presetInput${id}" ${boolToDisabledAttr(disabled)}>`;
            break;
        case PresetFieldType.NUMBER:
            val += `<input class="form-control" ${validator} type="number" name="ddp_${field.name}" value="${initValue}" id="presetInput${id}" ${boolToDisabledAttr(disabled)}>`;
            break;
        case PresetFieldType.RANGE:
            val += createRangePresetFormField(field, id, initValue as number, disabled);
            break;
        case PresetFieldType.BOOL:
            val += creteBoolPresetFormField(initValue, id, disabled);
            break;
        case PresetFieldType.ENUM:
            val += creteEnumPresetFormField(field, id, initValue, disabled);
            break;
    }
    val += `<p class="form-text text-danger" id="form-value-error-msg${id}"></p>`
    if (field.description) {
        val += `<div class="form-text">${field.description}</div>`
    }
    val += '</div>';
    return val;
}

export function updateRangeValText(rangeElem: HTMLInputElement, id: number, minVal: number, maxVal: number, type: SliderType, unit: string = '') {
    const target = document.getElementById('rangeVal' + id);
    if (target) {
        if (type === SliderType.LINEAR) {
            target.innerText = formatSIUnitNumber(rangeElem.valueAsNumber, 2, unit);
        }
        else if (type === SliderType.LOGARITHMIC) {
            target.innerText = formatSIUnitNumber(logarithmicValueFromPos(rangeElem.valueAsNumber, minVal, maxVal), 2, unit);
        }
        validateField(rangeElem.name.slice(4), rangeElem, id)
    }
}

export function setErrorMessage(id: number, message: string) {
    const errorElem = document.getElementById('form-value-error-msg' + id);
    if (errorElem) {
        errorElem.innerHTML = message;
    }
}

export function getErrorMessage(id: number): string {
    const errorElem = document.getElementById('form-value-error-msg' + id);
    if (errorElem) {
        return errorElem.innerHTML;
    } else {
        return '';
    }
}

function boolToDisabledAttr(disabled: boolean): string {
    return disabled ? 'disabled' : '';
}

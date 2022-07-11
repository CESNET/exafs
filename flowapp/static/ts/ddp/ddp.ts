import {stringToHtml, attachHtmlTo} from '../renderer';
import {DDPPreset, DDPPresetField, PresetFieldType} from "./ddp_presets";
import {formatSIUnitNumber} from "../utils";
import {logarithmicValueFromPos} from "./logscale";

export function shouldRenderPresetSelectionForm(actionSelect: HTMLSelectElement, requiredTitle: string): boolean {
    return actionSelect.options[actionSelect.selectedIndex].text === requiredTitle;
}

export function updateRangeValText(rangeElem: HTMLInputElement, targetId: string, minVal: number, maxVal: number, unit: string = '') {
    const target = document.getElementById(targetId);
    if (target) {
        target.innerText = formatSIUnitNumber(logarithmicValueFromPos(rangeElem.valueAsNumber, minVal, maxVal), 2, unit);
    }
}

export function presetSelectionChanged(preset: DDPPreset) {

}

function createPresetInputs(data: DDPPresetField[]): string {
    let form = '';
    let id = 0;
    for (let field of data) {
        form += createPresetField(field, id);
        id++;
    }
    return form;
}

function wrapField(field: string, id: number): string {
    return `<div class="row my-1" id="fieldContainer${id}">${field}</div>`;
}

function createPresetField(field: DDPPresetField, id: number): string {
    let fld = '';
    switch (field.type) {
        case PresetFieldType.TEXT:
            break;
        case PresetFieldType.NUMBER:
            break;
        case PresetFieldType.RANGE:
            break;
        case PresetFieldType.BOOL:
            break;
        case PresetFieldType.ENUM:
            break;
    }
    return wrapField(fld, id);
}

function createTextPresetField(field: DDPPresetField, id: number): string {
    return `<input type="text" id="">`
}

function createNumberPresetField(field: DDPPresetField, id: number): string {
    return `<input type="number" id="">`
}

function createRangePresetField() {

}



export function createTestComponent(heading: string) {
    const component = `<div class="row">
            <div class="col-12">
                <h1>${heading}</h1>
            </div>
        </div>
    `;
    attachHtmlTo(stringToHtml(component), 'ddp');
}
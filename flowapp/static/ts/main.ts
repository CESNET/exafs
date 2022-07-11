import {register_listeners} from "./global_listeners";

export {
    switchFocusOnKeypress,
    fillOrganization,
    changeAllCheckboxes,
    hideFieldIfNot
} from './forms'
export {createTestComponent, updateRangeValText} from './ddp/ddp'

export {initEditPresetsForm, presetFormAddField, rebuildDropdowns, updatePresetFormField, removeField, savePreset, onPresetNameChange} from './ddp/edit_preset'
export {showPreset} from './ddp/ddp_presets';

window.onload = function () {
    register_listeners();
}

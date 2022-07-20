import {register_listeners} from "./global_listeners";

export {
    switchFocusOnKeypress,
    fillOrganization,
    changeAllCheckboxes,
    hideFieldIfNot
} from './forms'
export {updateRangeValText} from './ddp/inputs'

export {
    addBeforeUnloadEventListener,
    initEditPresetsForm,
    presetFormAddField,
    onRuleTypeChange,
    updatePresetFormField,
    removeField,
    savePreset,
    onPresetNameChange
} from './ddp/edit_preset'
export {showPreset} from './ddp/ddp_presets';
export {initSelectPresetForm, changeAdvancedOptionsText, beforeIPFormSend} from './ddp/select_preset';
export {validateField} from './ddp/validators'

window.onload = function () {
    register_listeners();
}

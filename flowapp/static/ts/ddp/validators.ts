import {setErrorMessage} from "./inputs";
import {getValidatorsByType} from "./ddp_presets";

export interface Validator {
    options?: any;
    validate(value: any): boolean;
    invalidMessage(): string
}

export class NumberRangeValidator implements Validator {
    options: { min?: number, max?: number }

    constructor(min?: number, max?: number) {
        this.options = {min: min, max: max};
    }

    validate(value: number): boolean {
        let valid = true;
        if (this.options.min !== undefined && value < this.options.min) {
            valid = false;
        }
        if (this.options.max !== undefined && value > this.options.max) {
            valid = false;
        }
        return valid;
    }

    invalidMessage(): string {
        return `Value has to be in range ${this.options.min} - ${this.options.max}`;
    }
}

export class RegexPatternValidator implements Validator {
    options: {
        readonly regex: RegExp,
        name?: string,
        hint?: string
    }

    constructor(regex: RegExp, name?: string, hint?: string) {
        this.options = {regex: regex, name: name, hint: hint};
    }

    validate(value: string): boolean {
        const re = new RegExp(this.options.regex)
        return re.test(value);
    }

    invalidMessage(): string {
        let message = 'Invalid format'
        if (this.options.name) {
            message += ' for ' + this.options.name
        }
        if (this.options.hint) {
            message += ' - ' + this.options.hint;
        }
        return message;
    }
}

export class NonZeroValidator implements Validator {
    validate(value: string | number): boolean {
        return (+value) !== 0;
    }

    invalidMessage(): string {
        return 'This field can not be zero.';
    }
}


export function validateField(field_name: string, fieldRef: HTMLInputElement | HTMLSelectElement, id: number) {
    const validators = getValidatorsByType(field_name);
    if (validators) {
        let messages = '';
        let valid = true;
        for (let v of validators) {
            if (!v.validate(fieldRef.value)) {
                valid = false;
                messages += v.invalidMessage() + '<br>';
            }
        }
        setErrorMessage(id, messages);
        if (!valid) {
            fieldRef.classList.add('is-invalid');
        } else {
            fieldRef.classList.remove('is-invalid');
        }
    }
}
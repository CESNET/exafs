import {Modal} from "bootstrap";
import {formatSIUnitNumber} from "../utils";
import {NonZeroValidator, NumberRangeValidator, RegexPatternValidator, Validator} from './validators'

export type DDPPreset = {
    name: string;
    id: number;
    editable: string[];
    fields: {
        rule_type: DDPRuleType;
        threshold_bps?: number;
        threshold_pps?: number;
        vlan?: number;
        protocol?: string;
        threshold_syn_soft?: number;
        threshold_syn_hard?: number;
        fragmentation?: string;
        packet_lengths?: string;
        limit_bps?: number;
        limit_pps?: number;
        validity_timeout?: string;
        algorithm_type?: string;
        table_exponent?: number;
    }
}

export enum SliderType {
    LINEAR,
    LOGARITHMIC
}

export enum DDPRuleType {
    AMPLIFICATION = 'amplification',
    SYN_DROP = 'syn_drop',
    FILTER = 'filter',
    TCP_AUTHENTICATOR = 'tcp_authenticator'
}

export enum PresetFieldType {
    TEXT = 'text',
    NUMBER = 'number',
    RANGE = 'range',
    BOOL = 'bool',
    ENUM = 'enum'
}

export enum PresetFieldRequirementRelationship {
    IsSet,
    IsNotSet,
    IsGreater,
    IsLower,
    IsGreaterOrEqual,
    IsLowerOrEqual,
    IsEqual,
    IsNotEqual,
}

export type EnumPresetFieldOpts = {
    values: string[] | { value: any, display: string }[];
    multi: boolean;
}

export type RangePresetFieldOpts = {
    low: number;
    high: number;
    unit: string;
    type: SliderType;
}

export type DDPPresetField = {
    printName: string;
    name: string
    description?: string;
    formId?: number;
    defaultValue: any;
    type: PresetFieldType;
    rule_types: DDPRuleType[];
    options?: EnumPresetFieldOpts | RangePresetFieldOpts;
    validators?: Validator[];
    requires_fields?: [{ name: string, relationship: PresetFieldRequirementRelationship, rule_types: DDPRuleType[] }]
}

export const AVAILABLE_PRESET_FIELDS: DDPPresetField[] = [
    {
        name: 'threshold_bps',
        printName: 'Threshold [bits/s]',
        type: PresetFieldType.RANGE,
        defaultValue: 0,
        description: 'Activate rule when traffic reaches the given threshold defined by bits per second. Bits per second are calculated on L2 without Ethernet FCS field (4B).',
        options: {low: 100000000, high: 100000000000, unit: 'b/s', type: SliderType.LOGARITHMIC},
        rule_types: [DDPRuleType.AMPLIFICATION, DDPRuleType.FILTER, DDPRuleType.SYN_DROP, DDPRuleType.TCP_AUTHENTICATOR],
        requires_fields: [{
            name: 'limit_bps',
            relationship: PresetFieldRequirementRelationship.IsLowerOrEqual,
            rule_types: [DDPRuleType.AMPLIFICATION]
        }]
    },
    {
        name: 'threshold_pps',
        printName: 'Threshold [packets/s]',
        type: PresetFieldType.RANGE,
        defaultValue: 0,
        description: 'Activate rule when traffic reaches the given threshold defined by packets per second.',
        options: {low: 10000, high: 1000000000, unit: ' packet/s', type: SliderType.LOGARITHMIC},
        rule_types: [DDPRuleType.AMPLIFICATION, DDPRuleType.FILTER, DDPRuleType.SYN_DROP, DDPRuleType.TCP_AUTHENTICATOR],
        requires_fields: [{
            name: 'limit_pps',
            relationship: PresetFieldRequirementRelationship.IsLowerOrEqual,
            rule_types: [DDPRuleType.AMPLIFICATION]
        }]
    },
    {
        name: 'protocol',
        printName: 'Protocol',
        type: PresetFieldType.ENUM,
        defaultValue: '',
        description: 'List of L4 protocols. If not set, apply to all.',
        rule_types: [DDPRuleType.FILTER, DDPRuleType.AMPLIFICATION],
        options: {values: ['TCP', 'UDP', 'ICMP', 'SCTP'], multi: true},
    },
    {
        name: 'tcp_flags',
        printName: 'TCP Flags',
        type: PresetFieldType.TEXT,
        defaultValue: '',
        description: 'List of TCP flags combinations. Combinations can be created using following values:' +
            '<ul><li>C: Congestion window reduced,</li>' +
            '<li>E: ECN-Echo,</li>' +
            '<li>U: Urgent,</li>' +
            '<li>A: Acknowledge,</li>' +
            '<li>P: Push,</li>' +
            '<li>R: Reset,</li>' +
            '<li>S: Synchronize,</li>' +
            '<li>F: Finalize.</li></ul>' +
            'Using these a packet is accepted only if the corresponding flag is set. If a letter is negated using ‘!’ a packet is accepted only if the corresponding flag is not set. Otherwise a value of a flag does not matter.' +
            '<br>Example for SYN and SYN+ACK packets only: !C!E!U!P!RS!F',
        rule_types: [DDPRuleType.AMPLIFICATION],
        // Regex: "(?!.*?([CEUAPRSF]).*\1)" (first part): Use a lookahead to check, if there is only one of each character
        // "(!?[CEUAPRSF]){1,8}" (second part):  Match any of the valid letters (CEUAPRSF), with an optional exclamation mark in front of it.
        validators: [new RegexPatternValidator(/^(?!.*?([CEUAPRSF]).*\1)(!?[CEUAPRSF]){1,8}$/gm, 'TCP Flags',
            'value can only contain letters C, E, U, A, P, R, S and F, optionally prefixed by exclamation mark (!C), each letter only once. Check the description for an example.')]
    },
    {
        name: 'vlan', printName: 'VLAN ID', type: PresetFieldType.NUMBER, defaultValue: 0,
        description: 'VLAN ID. If zero, match only packets without VLAN ID.',
        rule_types: [DDPRuleType.AMPLIFICATION, DDPRuleType.FILTER, DDPRuleType.SYN_DROP, DDPRuleType.TCP_AUTHENTICATOR]
    },
    {
        name: 'threshold_syn_soft',
        printName: 'Soft SYN threshold',
        type: PresetFieldType.RANGE,
        defaultValue: 5,
        description: 'Number of SYN-only packets (per client) that are allowed without receiving any ACK-only packet.',
        options: {low: 2, high: 10, unit: 'packets', type: SliderType.LINEAR},
        rule_types: [DDPRuleType.SYN_DROP]
    },
    {
        name: 'threshold_syn_hard',
        printName: 'Hard SYN threshold',
        type: PresetFieldType.RANGE,
        defaultValue: 20,
        description: 'Number of packets (per client) after which all consequent SYN-only packets are dropped regardless of received ACK packets.',
        options: {low: 2, high: 100, unit: 'packets', type: SliderType.LINEAR},
        rule_types: [DDPRuleType.SYN_DROP, DDPRuleType.TCP_AUTHENTICATOR]
    },
    {
        name: 'limit_bps',
        printName: 'Limit [bits/s]',
        defaultValue: 0,
        description: 'Traffic volume defined as bits per second. Defines how much traffic will be allowed to the protected network during an attack.' +
            ' Traffic from N biggest contributors is blocked until traffic volume is limited to or below this target value. Bits per second are calculated on L2 without Ethernet FCS field (4B).' +
            ' A limit value has to be lower or equal to corresponding threshold value.',
        rule_types: [DDPRuleType.AMPLIFICATION],
        type: PresetFieldType.RANGE,
        options: {low: 100000000, high: 100000000000, unit: 'b/s', type: SliderType.LOGARITHMIC},
        validators: [new NonZeroValidator()],
        requires_fields: [{
            name: 'threshold_bps',
            relationship: PresetFieldRequirementRelationship.IsGreaterOrEqual,
            rule_types: [DDPRuleType.AMPLIFICATION]
        }]
    },
    {
        name: 'limit_pps',
        printName: 'Limit [packets/s]',
        defaultValue: 1000000,
        description: 'Traffic volume amount defined as packets per second. Says how much traffic will be limited during an attack. N biggest contributors are blocked until traffic volume is limited to this value.',
        rule_types: [DDPRuleType.AMPLIFICATION],
        type: PresetFieldType.RANGE,
        options: {low: 10000, high: 1000000000, unit: ' packet/s', type: SliderType.LOGARITHMIC},
        validators: [new NonZeroValidator()],
        requires_fields: [{
            name: 'threshold_pps',
            relationship: PresetFieldRequirementRelationship.IsGreaterOrEqual,
            rule_types: [DDPRuleType.AMPLIFICATION]
        }]
    },
    {
        name: 'fragmentation',
        printName: 'Fragmentation',
        type: PresetFieldType.ENUM,
        defaultValue: 'ANY',
        description: 'Specification of packets from the fragmentation point of view.',
        rule_types: [DDPRuleType.AMPLIFICATION],
        options: {values: ['ANY', 'NO', 'YES', 'FIRST', 'LAST', 'MIDDLE', 'NOFIRST'], multi: false}
    },
    {
        name: 'packet_lengths',
        printName: 'Packet lengths [B]',
        defaultValue: '',
        description: 'List of packet lengths and packet lengths ranges. Only packets of matching length are considered.' +
            ' If empty, packets of any length are considered. L2 packet length without FCS field (4B) is considered. Possible values: x;&gt;x;x-y;&lt;x;&lt;=x;&gt;=x',
        type: PresetFieldType.TEXT,
        rule_types: [DDPRuleType.AMPLIFICATION]
    },
    {
        name: 'validity_timeout',
        printName: 'Validity timeout',
        rule_types: [DDPRuleType.TCP_AUTHENTICATOR],
        type: PresetFieldType.RANGE,
        defaultValue: 1,
        description: 'Maximum validity interval of host (i.e. source IP address) authentication. If a host tries to establish another TCP connection after the timeout has elapsed, it must be authenticated again.',
        options: {low: 1, high: 600, unit: 's', type: SliderType.LINEAR}
    },
    {
        name: 'algorithm_type',
        printName: 'Algorithm type',
        type: PresetFieldType.ENUM,
        defaultValue: 'RST_COOKIES',
        description: 'Type of algorithm to be used for mitigation:' +
            '<ul><li>RST_COOKIES: Reset Cookies algorithm,</li>' +
            '<li>SYN_AUTH: SYN Authentication algorith</li></ul>',
        rule_types: [DDPRuleType.TCP_AUTHENTICATOR],
        options: {values: ['RST_COOKIES', 'SYN_AUTH'], multi: false}
    },
    {
        name: 'table_exponent',
        printName: 'Table exponent',
        type: PresetFieldType.NUMBER,
        defaultValue: 18,
        description: 'Size exponent (i.e. 2^x) of the record table. It corresponds to maximum number of unique source IP addresses.',
        rule_types: [DDPRuleType.SYN_DROP, DDPRuleType.AMPLIFICATION, DDPRuleType.TCP_AUTHENTICATOR],
        validators: [new NumberRangeValidator(10, 30)]
    }
];

type FieldsRequiredByRuleType = {[key in DDPRuleType]: string[]}

export const REQUIRED_FIELDS_BY_RULE_TYPE: FieldsRequiredByRuleType = {
    [DDPRuleType.AMPLIFICATION]: [],
    [DDPRuleType.SYN_DROP]: ['threshold_syn_soft', 'threshold_syn_hard'],
    [DDPRuleType.FILTER]: [],
    [DDPRuleType.TCP_AUTHENTICATOR]: ['validity_timeout', 'algorithm_type']
}

/***
 * Get field information based on the rule field name from database
 *
 * @param {string} key - DDoS Protector rule field name from database
 * @returns {DDPPresetField} - Information about the field, such as human-readable name,
 *                             type of the input field, supported rule types and more
 *                             (additional information in the `options` field based on input type)
 * */
export function getPresetField(key: string): DDPPresetField | undefined {
    return AVAILABLE_PRESET_FIELDS.find((field) => {
        return field.name === key
    })
}

/***
 * Get all preset fields that can be included with given rule type
 *
 * @param {DDPRuleType} ruleType - Find fields that support this rule type
 * @returns {DDPPresetField[]}   - Subset of all available fields, where the `rule_types` attribute
 *                                 includes given rule type.
 * */
export function getPresetFieldsByRuleType(ruleType: DDPRuleType): DDPPresetField[] {
    return AVAILABLE_PRESET_FIELDS.filter((field) => {
        return field.rule_types?.includes(ruleType);
    })
}

export function showPreset(title: string, fields: any[], editable: string[]) {
    const titleElem = document.getElementById('presetDetailTitle');
    const bodyElem = document.getElementById('presetDetailBody') as HTMLTableElement;
    const modalElem = document.getElementById('presetDetailModal');
    if (titleElem && bodyElem && modalElem) {
        titleElem.innerHTML = title;
        bodyElem.innerHTML = '';
        for (let key in fields) {
            let row = bodyElem.insertRow(bodyElem.rows.length);
            let keyCell = row.insertCell();
            let valCell = row.insertCell();
            let editableCell = row.insertCell();
            keyCell.innerHTML = key;
            if (typeof fields[key] === 'number') {
                valCell.innerHTML = formatSIUnitNumber(fields[key] as number, 2, '');
            } else {
                valCell.innerHTML = fields[key].toString();
            }
            editableCell.innerHTML = editable.includes(key) ? 'Yes' : 'No';
        }
        let modal = new Modal(modalElem, {backdrop: true, keyboard: true});
        modal.show();
    }
}

export function getValidatorsByType(key: string): Validator[] | undefined {
    const field = getPresetField(key);
    if (field) {
        return field.validators;
    } else {
        return undefined;
    }

}
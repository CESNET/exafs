/***
 * Format a number to an SI unit format. Only supports unit prefixes k, M, G and T.
 * @example
 * // returns '25.1 Mbps'
 * formatSIUnitNumber(25100015, 2, 'bps');
 *
 * @param {number} num         - Number to format
 * @param {number} maxDecimals - Maximum number of decimal spaces
 * @param {string} unit        - Optional unit to put after the number. Empty string by default.
 *
 * @returns {string}           - `num` with an SI prefix, rounded to specified number of decimals.
 */
export function formatSIUnitNumber(num: number, maxDecimals: number, unit: string = ''): string {
    if (num >= 1000000000000) {
        return (roundToPrecision(num / 1000000000000, maxDecimals)).toString() + ' T' + unit;
    } else if (num >= 1000000000) {
        return (roundToPrecision(num / 1000000000, maxDecimals)).toString() + ' G' + unit;
    } else if (num >= 1000000) {
        return (roundToPrecision(num / 1000000, maxDecimals)).toString() + ' M' + unit;
    } else if (num >= 1000) {
        return (roundToPrecision(num / 1000, maxDecimals)).toString() + ' k' + unit;
    } else {
        return (roundToPrecision(num, maxDecimals)).toString() + ' ' + unit;
    }
}

/***
 * Round a number to the specified number of decimals.
 * @example
 * // returns 12.35
 * roundToPrecision(12.3456789, 2)
 *
 * @param {number} value     - value to round
 * @param {number} precision - number of decimals to round to
 * @returns {number}         - `value` rounded to `precision` decimals
 */
function roundToPrecision(value: number, precision: number): number {
    const multiplier = Math.pow(10, precision || 0);
    return Math.round(value * multiplier) / multiplier;
}
/***
 * Convert a linear number between 0 and 100 to a logarithmic scale
 * in range `minVal` to `maxVal`. Used to convert linear range sliders
 * to a logarithmic scale.
 *
 * @param {number} pos    - Position of the slider (linearly scaling number from 0 to 100)
 * @param {number} minVal - Minimum output value - pos=0 converts to this value
 * @param {number} maxVal - Maximum output value - pos=100 converts to this value
 *
 * @returns {number} - Logarithmically scaling number from `minVal` to `maxVal` based on `pos`.
 * */
export function logarithmicValueFromPos(pos: number, minVal: number, maxVal: number): number {
    if (pos <= 0) {
        return 0;
    }
    const min = Math.log(Math.max(minVal, 1));
    const max = Math.log(maxVal);
    const scale = (max - min) / 100; // max-min value / max-min position (100-0 = 0)
    return Math.round(Math.exp(pos * scale + min));
}

/***
 * Convert logarithmic number in range from `minVal` to `maxVal` into a number
 * between 0 - 100 in a linear scale. Can be used to set a range slider position
 * based on a logarithmic number.
 *
 * @param {number} val    - Value to convert - in range from `minVal` to `maxVal`
 * @param {number} minVal - Minimum output value - if val=minVal, returns 0
 * @param {number} maxVal - Maximum output value - if val=maxVal, returns 100
 *
 * @returns {number} - Linearly scaling number from 0 to 100 based on `val`.
 */
export function posFromLogarithmicValue(val: number, minVal: number, maxVal: number): number {
    if (val <= 0) {
        return 0;
    }
    const min = Math.log(Math.max(minVal, 1));
    const max = Math.log(maxVal);
    const scale = (max - min) / 100; // max-min value / max-min position (100-0 = 0)
    return Math.round((Math.log(val) - min) / scale);
}
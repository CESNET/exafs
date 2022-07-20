/***
 * Send FormData to a specified url. If the request is successful,
 * the `callbackSuccess` callback is called, otherwise the `callbackFail` is called.
 *
 * @param {FormData} data - data to send to the `url`.
 * @param {string} url - URL to send the data to.
 * @param {string} method - HTTP method to use. Valid values are "POST", "GET", "PUT", "PATCH", and "DELETE.
 * */
export function sendFormDataToBackend(data: FormData, url: string, method: string): Promise<Response> {
    const requestOpts: RequestInit = {
        method: method.toUpperCase(), //"POST",
        body: data
    };
    return fetch(url, requestOpts)
}
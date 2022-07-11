/***
 * Send FormData to a specified url. If the request is successful,
 * the `callbackSuccess` callback is called, otherwise the `callbackFail` is called.
 *
 * @param {FormData} data - data to send to the `url`.
 * @param {string} url - URL to send the data to.
 * @param {string} method - HTTP method to use. Valid values are "POST", "GET", "PUT", "PATCH", and "DELETE.
 * @param {(response: Response) => void} callbackSuccess - Function to call if the request was successful
 * @param {(error: string) => void} callbackFail - Function to call if the request was not successful
 * */
export function sendToBackend(data: FormData, url: string, method: string, callbackSuccess: (response: Response) => void, callbackFail: (error: string) => void) {
    const requestOpts: RequestInit = {
        method: method, //"POST",
        body: data
    };
    console.log('sending data:');
    console.log(data);
    fetch(url, requestOpts)
        .then(response => callbackSuccess(response))
        .catch(error => callbackFail(error));
}
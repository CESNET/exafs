document.getElementById("check-all").addEventListener("click", function(event){
    /**
     * find all checkboxes in current dashboard and toggle checked all / none
     */
    const inputs = document.querySelectorAll("input[type='checkbox']");
    if (this.checked) {
        for(let minput of inputs) {
            minput.checked = true;   
        }
    } else {
        for(let minput of inputs) {
            minput.checked = false;   
        }
    }
});
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.btn-close[data-clear-url]').forEach(btn => {
        btn.addEventListener('click', function() {
            window.location.href = this.dataset.clearUrl;
        });
    });

    const searchInput = document.querySelector('input[name="squery"]');
    if (searchInput) {
        const clearUrl = searchInput.dataset.clearUrl;
        
        searchInput.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && this.value && clearUrl) {
                window.location.href = clearUrl;
            }
        });
    }
});

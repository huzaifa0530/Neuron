$(document).ajaxError(function(event, jqxhr, settings, thrownError) {
    if (jqxhr.status === 401) {
        try {
            const response = JSON.parse(jqxhr.responseText);
            if (response.redirect) {
                alert(response.message || "Session expired. Redirecting to login...");
                window.location.href = '/accounts/login/';
            }
        } catch (e) {
            console.error("401 error received but failed to parse JSON.");
            window.location.href = '/accounts/login/';
        }
    }
});

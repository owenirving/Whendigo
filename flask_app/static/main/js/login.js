function checkCredentials() {
    // Get credientials from the form
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;

    var data_d = { email: email, password: password };

    // Send data to server
    jQuery.ajax({
        url: "/processlogin",
        data: data_d,
        type: "POST",
        success: function (retruned_data) {
            retruned_data = JSON.parse(retruned_data);

            if (retruned_data.success === 1) {
                window.location.href = "/";
            } else {
                alert(retruned_data.message);
            }
        },
    });
}

document.getElementById("submit").addEventListener("click", function (event) {
    event.preventDefault();
    checkCredentials();
});

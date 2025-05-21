function createAccount() {
    // Get credientials from the form
    const name = document.getElementById("name").value;
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;
    const confirmPassword = document.getElementById("confirm").value;

    // Ensure passwords match and are at least 8 characters long
    if (password.length < 8) {
        alert("Password must be at least 8 characters long");
        return;
    }
    if (password !== confirmPassword) {
        alert("Passwords do not match");
        return;
    }

    var data_d = { name: name, email: email, password: password };

    // Send data to server
    jQuery.ajax({
        url: "/processregister",
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

// Submit button event listener
document.getElementById("submit").addEventListener("click", function (event) {
    event.preventDefault();
    createAccount();
});

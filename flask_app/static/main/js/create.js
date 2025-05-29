function createEvent() {
    // Get event info from the form
    const name = document.getElementById("name").value;
    const start_date = document.getElementById("start_date").value;
    const end_date = document.getElementById("end_date").value;
    const start_time = document.getElementById("start_time").value;
    const end_time = document.getElementById("end_time").value;
    const invitees = document.getElementById("invitees").value;

    // Ensure end date/time is after start date/time
    if (end_date < start_date) {
        alert("End date must be after start date");
        return;
    }
    if (end_time < start_time) {
        alert("End time must be after start time");
        return;
    }

    var data_d = {
        name: name,
        start_date: start_date,
        end_date: end_date,
        start_time: start_time,
        end_time: end_time,
        invitees: invitees,
    };

    // send data to server
    jQuery.ajax({
        url: "/processcreate",
        data: JSON.stringify(data_d),
        contentType: "application/json",
        type: "POST",
        success: function (returned_data) {
            returned_data = JSON.parse(returned_data);

            if (returned_data.success === 1) {
                window.location.href = "/event/" + returned_data.event_id;
            } else {
                alert(returned_data.message);
            }
        },
    });
}

// submit button event listener
document.getElementById("submit").addEventListener("click", function (event) {
    event.preventDefault();
    createEvent();
});

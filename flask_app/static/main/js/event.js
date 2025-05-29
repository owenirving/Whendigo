document.addEventListener("DOMContentLoaded", () => {
    // Initialize connection and variables
    const socket = io("/event");
    const event = typeof event_info !== "undefined" ? event_info : {};
    const grid = document.getElementById("availability-grid");
    const modeSelect = document.getElementById("mode");
    const eventId = window.location.pathname.split("/").pop();
    let userAvailability = {};
    let groupAvailability = {};
    let dragging = false;
    let selected = [];

    // Get initial data and add it to the grid
    fetch(`/api/event/${eventId}/availability`)
        .then((res) => res.json())
        .then(({ user_availability, group_availability, best_time }) => {
            userAvailability = Object.fromEntries(
                user_availability.map(({ slot_date, slot_time, status }) => [
                    `${slot_date} ${slot_time}`,
                    status,
                ])
            );
            groupAvailability = group_availability;
            makeGrid();
            updateBestTime(best_time);
        });

    // Generate time range in 30-minute increments
    function getTimeRange(startTime, endTime, startDate) {
        const times = [];

        let current = new Date(`${startDate}T${startTime}`);
        const end = new Date(`${startDate}T${endTime}`);

        while (current < end) {
            // Add time to times list
            const hours = String(current.getHours()).padStart(2, "0");
            const minutes = String(current.getMinutes()).padStart(2, "0");
            times.push(`${hours}:${minutes}`);

            // Increment by 30 minutes
            current.setMinutes(current.getMinutes() + 30);
        }
        return times;
    }

    // Generate date range
    function getDateRange(startDate, endDate) {
        const dates = [];
        let current = new Date(startDate);
        let end = new Date(endDate);

        // Increment start and end dates by one to get the correct range
        current.setDate(current.getDate() + 1);
        end.setDate(end.getDate() + 1);

        // Add all dates in the range to the dates list
        while (current <= end) {
            dates.push(new Date(current));
            current.setDate(current.getDate() + 1);
        }
        return dates;
    }

    // make grid
    function makeGrid() {
        const startDate = event.start_date;
        const endDate = event.end_date;
        const startTime = event.start_time.padStart(8, "0").slice(0, 5);
        const endTime = event.end_time.padStart(8, "0").slice(0, 5);
        const dates = getDateRange(startDate, endDate);
        const times = getTimeRange(startTime, endTime, startDate);

        grid.innerHTML = "";
        // Set up header row (one for each date)
        let header = "<tr><th>Time</th>";
        dates.forEach((date) => {
            header += `<th>${date.toLocaleDateString("en-US", {
                weekday: "short",
                month: "short",
                day: "numeric",
            })}</th>`;
        });
        header += "</tr>";
        grid.innerHTML += header;

        // Time slot rows (one for each time slot)
        times.forEach((time) => {
            let row = `<tr><td>${time}</td>`;
            dates.forEach((date) => {
                const slotDate = date.toISOString().slice(0, 10);
                const slotKey = `${slotDate} ${time}:00`;
                const groupStatus = getGroupStatus(slotKey);
                row += `<td class="${groupStatus}" data-date="${slotDate}" data-time="${time}:00"></td>`;
            });
            row += "</tr>";
            grid.innerHTML += row;
        });

        // Add event listeners
        grid.querySelectorAll("td:not(:first-child)").forEach((cell) => {
            cell.addEventListener("mousedown", startDrag);
            cell.addEventListener("mouseover", continueDrag);
            cell.addEventListener("mouseup", endDrag);
            cell.addEventListener("click", click);
        });
    }

    // End drag when mouse is released
    document.addEventListener("mouseup", endDrag);

    // Determine group status for heatmap
    function getGroupStatus(slotKey) {
        const counts = groupAvailability[slotKey] || {
            available: 0,
            maybe: 0,
            unavailable: 0,
        };
        //console.log(counts);
        if (counts.available > 0) {
            if (counts.available >= 3) return "available-3";
            if (counts.available === 2) return "available-2";
            return "available-1";
        }
        if (counts.maybe > 0) return "maybe";
        if (counts.unavailable > 0) return "unavailable";

        return "unset";
    }

    // Update grid with new group availability
    function updateGrid(newGroupAvailability) {
        groupAvailability = newGroupAvailability;
        grid.querySelectorAll("td:not(:first-child)").forEach((cell) => {
            const slotKey = `${cell.dataset.date} ${cell.dataset.time}`;
            const groupStatus = getGroupStatus(slotKey);
            cell.className = groupStatus;
        });
    }

    // Update best time section
    function updateBestTime(bestTime) {
        const bestTimeText = document.getElementById("best_time");
        // Display no times submitted yet message
        if (bestTime.message) {
            bestTimeText.textContent = bestTime.message;
            // Display best time
        } else {
            date = new Date(bestTime.date);
            date.setDate(date.getDate() - 1);
            date = date.toISOString().slice(0, 10);
            bestTimeText.textContent = `${date} ${bestTime.start.slice(
                0,
                5
            )} – ${bestTime.end.slice(10, 16)}`;
        }
    }

    // Get slot from event
    function getSlotFromEvent(event) {
        return {
            slot_date: event.target.dataset.date,
            slot_time: event.target.dataset.time,
        };
    }

    // Start drag event
    function startDrag(event) {
        dragging = true;
        const slot = getSlotFromEvent(event);
        selected = [slot];
        const status = modeSelect.value;
        event.target.classList.add("selected-mode");
        updateSlots([slot], status);
    }

    // Continue drag event selecting slots it moves over
    function continueDrag(event) {
        if (dragging) {
            const slot = getSlotFromEvent(event);
            if (
                !selected.some(
                    (s) =>
                        s.slot_date === slot.slot_date &&
                        s.slot_time === slot.slot_time
                )
            ) {
                selected.push(slot);
                event.target.classList.add("selected-mode");

                const status = modeSelect.value;
                updateSlots([slot], status);
            }
        }
    }

    // End drag event
    function endDrag() {
        if (dragging) {
            dragging = false;
            selected = [];
            grid.querySelectorAll(".selected-mode").forEach((cell) =>
                cell.classList.remove("selected-mode")
            );
            selected = [];
        }
    }

    // Handle click event
    function click(event) {
        const slot = getSlotFromEvent(event);
        const status = modeSelect.value;
        updateSlots([slot], status);
    }

    // Update slots
    function updateSlots(slots, status) {
        const formattedSlots = slots.map((slot) => ({
            slot_date: slot.slot_date,
            slot_time: slot.slot_time,
        }));

        fetch(`/api/event/${eventId}/availability`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ slots: formattedSlots, status }),
        })
            .then((res) => res.json())
            .then((data) => {
                if (data.success) {
                    slots.forEach((slot) => {
                        const slotKey = `${slot.slot_date} ${slot.slot_time}`;
                        userAvailability[slotKey] = status;
                        const cell = grid.querySelector(
                            `td[data-date="${slot.slot_date}"][data-time="${slot.slot_time}"]`
                        );
                        if (cell) {
                            cell.className = getGroupStatus(slotKey);
                        }
                    });
                }
            });
    }

    // Update grid with availability data
    socket.on("availability_update", (data) => {
        updateGrid(data.group_availability);
        updateBestTime(data.best_time);
    });

    // Add user to event
    socket.on("connect", () => {
        socket.emit("join_event", { event_id: event_id });
    });
});

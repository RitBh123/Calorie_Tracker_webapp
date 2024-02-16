document.addEventListener("DOMContentLoaded", function() {
    document.getElementById("food").addEventListener("change", function() {
        try {
            // Get the selected food item
            var selectedOption = this.options[this.selectedIndex];

            // Update the calorie and serving description fields
            var calories = selectedOption.dataset.calories;
            var servingDescription = selectedOption.dataset.servingdescription;

            console.log("Calories:", calories);
            console.log("Serving description:", servingDescription);

            document.getElementById("calories").value = calories || '';
            document.getElementById("serving_description").value = servingDescription || '';
        } catch (error) {
            console.error('An error occurred while updating food information:', error);
            // Handle the error here, e.g., show an alert to the user
            alert('An error occurred while updating food information. Please try again later.');
        }
    });
});

document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('activity_select').addEventListener('change', function() {
        try {
            var activity = this.value;
            var specificMotionSelect = document.getElementById('specific_motion_select');
            specificMotionSelect.innerHTML = '<option value="">Select Specific Motion</option>'; // Clear existing options
            if (activity !== '') {
                fetch('/specific_motions/' + activity)
                    .then(response => response.json())
                    .then(data => {
                        data.specific_motions.forEach(function(specificMotion) {
                            specificMotionSelect.innerHTML += '<option value="' + specificMotion + '">' + specificMotion + '</option>';
                        });
                        specificMotionSelect.disabled = false; // Enable specific motion dropdown
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        // Handle the error here, e.g., show an alert to the user
                        alert('An error occurred while fetching specific motions. Please try again later.');
                    });
            } else {
                specificMotionSelect.disabled = true; // Disable specific motion dropdown if no activity selected
            }
        } catch (error) {
            console.error('An error occurred while updating activity information:', error);
            // Handle the error here, e.g., show an alert to the user
            alert('An error occurred while updating activity information. Please try again later.');
        }
    });
});

function validateServings() {
    var servingsInput = document.getElementById("no_servings").value;
    var age = document.getElementById("age").value;
    var height = document.getElementById("height").value;
    var weight = document.getElementById("weight").value;
    try {
        if (!isWholeNumber(servingsInput)) {
            throw new Error("Please enter a number >= 1 and whole number for the number of servings.");
        } else if (!isWholeNumber(age)) {
            throw new Error("Please enter a number >= 1 and whole number for age.");
        } else if (!isWholeNumber(weight)) {
            throw new Error("Please enter a number >= 1 and whole number for weight.");
        } else if (!isWholeNumber(height)) {
            throw new Error("Please enter a number >= 1 and whole number for height.");
        }
        return true;
    } catch (error) {
        console.error('Validation error:', error);
        // Handle the error here, e.g., show an alert to the user
        alert(error.message);
        return false;
    }
}

function isWholeNumber(value) {
    return /^\d+$/.test(value);
}

document.addEventListener('DOMContentLoaded', function() {
    var thirtyDaysAgo = new Date();
    thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
    var thirtyDaysAgoStr = thirtyDaysAgo.toISOString().split('T')[0];
    var today = new Date().toISOString().split('T')[0];
    var dateInput = document.getElementById('date_input');
    dateInput.setAttribute('min', thirtyDaysAgoStr);
    dateInput.setAttribute('max', today);

    dateInput.addEventListener('input', function() {
        var selectedDate = new Date(this.value);
        if (selectedDate < thirtyDaysAgo || selectedDate > new Date()) {
            this.value = '';
        }
    });
});

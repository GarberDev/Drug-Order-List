$(document).ready(function () {
    // Toggle sidebar on button click
    $("#sidebarCollapse").on('click', function () {
        $("#sidebar").toggleClass('active');
    });

    // Close sidebar when a sidebar link is clicked
    $("#sidebar a").on('click', function () {
        $("#sidebar").addClass('active');
    });
});


// get details

document.addEventListener('DOMContentLoaded', function () {
    const getDetailsBtn = document.getElementById('get-details-btn');
    const medNameInput = document.getElementById('name');

    getDetailsBtn.addEventListener('click', function (e) {
        e.preventDefault();
        const medName = medNameInput.value;
        if (medName) {
            const detailsUrl = `/medications/details?name=${encodeURIComponent(medName)}`;
            window.location.href = detailsUrl;
        } else {
            alert('Please enter a medication name.');
        }
    });
});
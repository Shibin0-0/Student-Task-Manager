/**
 * main.js — Client-side helpers for Student Task Manager.
 *
 * Kept intentionally simple — no frameworks, no build step.
 * This file is loaded by base.html for every page.
 */

// ----------------------------------------------------------------
// Delete confirmation
//
// Every delete form on list.html has the class "delete-form" and
// its submit button carries a data-task-title attribute.
// We intercept the submit and ask the user to confirm before
// letting the form POST to the server.
// ----------------------------------------------------------------
document.addEventListener("DOMContentLoaded", function () {

    const deleteForms = document.querySelectorAll(".delete-form");

    deleteForms.forEach(function (form) {
        form.addEventListener("submit", function (event) {
            // Read the task title from the delete button's data attribute
            const btn       = form.querySelector("button[type='submit']");
            const taskTitle = btn ? btn.dataset.taskTitle : "this task";

            const confirmed = window.confirm(
                "Are you sure you want to delete:\n\n\"" + taskTitle + "\"\n\nThis cannot be undone."
            );

            if (!confirmed) {
                // Stop the form from submitting
                event.preventDefault();
            }
        });
    });

    // ----------------------------------------------------------------
    // Auto-dismiss flash alerts after 5 seconds
    // ----------------------------------------------------------------
    const alerts = document.querySelectorAll(".alert.alert-dismissible");

    alerts.forEach(function (alert) {
        setTimeout(function () {
            // Bootstrap 5's Collapse API handles the fade-out animation
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            if (bsAlert) {
                bsAlert.close();
            }
        }, 5000);   // 5 000 ms = 5 seconds
    });

});

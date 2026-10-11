

/*
  main.js — plain vanilla JavaScript. No framework, no build step,
  no external library. Everything else in this application (search,
  pagination, form submission, page navigation) is a plain HTML
  <form> or <a>, which the browser already handles correctly on its
  own by sending a request and loading the resulting page — reaching
  for JavaScript to reimplement something HTML already does natively
  is unnecessary complexity, and is deliberately avoided everywhere
  except this one place.

  The one genuine gap plain HTML cannot fill by itself is asking
  "are you sure?" before an irreversible action. There is no HTML
  attribute for that, so this is the one place JavaScript earns
  its inclusion in this project.
*/

document.addEventListener("DOMContentLoaded", function () {
    /*
      "DOMContentLoaded" is an event the browser fires once it has
      finished reading and building the entire page's structure
      from the HTML. Wrapping this script's logic inside this
      listener guarantees it only runs after every delete form on
      the page already exists — if this code ran immediately,
      before the page finished loading, querySelectorAll below
      could run too early and find nothing at all, since the
      elements it is looking for might not exist in the page yet
      at that exact moment.
    */

    const deleteForms = document.querySelectorAll(".js-confirm-delete");
    /*
      querySelectorAll searches the entire page for every element
      matching this CSS-style selector and returns all of them at
      once, as a list. This is exactly the class name given to
      each delete <form> back in templates/admin/dashboard.html —
      the dashboard can list any number of movies, each with its
      own identical delete form, and this one line finds every
      single one of them in a single pass, regardless of how many
      exist on the page.
    */

    deleteForms.forEach(function (form) {
        /*
          forEach runs the function that follows once for every
          item in the deleteForms list — once per delete form
          found on the page.
        */

        form.addEventListener("submit", function (event) {
            /*
              Attaches a listener to this specific form's "submit"
              event, which fires the instant someone clicks its
              Delete button, before the actual network request to
              the server is sent.
            */

            const confirmed = window.confirm(
                "Delete this movie? This cannot be undone, and will fail " +
                "if it still has ratings, tags, or links pointing to it."
            );
            /*
              window.confirm() shows the browser's own built-in
              popup dialog with OK and Cancel buttons, and pauses
              this script until the visitor responds. It returns
              true if they clicked OK, false if they clicked Cancel
              — that returned value is stored here in "confirmed".
            */

            if (!confirmed) {
                event.preventDefault();
                /*
                  event.preventDefault() stops this form's normal
                  submission from happening at all. It is called
                  only inside this "if not confirmed" branch —
                  meaning only when the visitor clicked Cancel. If
                  they clicked OK instead, this line never runs,
                  nothing is prevented, and the form submits exactly
                  as it would have with no script here at all. This
                  listener's only power is to stop the action; it
                  never changes what the action actually does when
                  allowed through.
                */
            }
        });
    });
});
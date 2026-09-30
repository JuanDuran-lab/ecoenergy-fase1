/*
 * Confirmación visual (SweetAlert2) antes de enviar un formulario de
 * eliminación. La seguridad real se valida en el servidor.
 */
document.addEventListener("submit", function (event) {
    const form = event.target;
    if (!form.classList.contains("js-confirm-delete") || form.dataset.confirmed === "true") {
        return;
    }
    event.preventDefault();

    const item = form.dataset.item || "este registro";
    const warning = form.dataset.warning;
    const text = `Se eliminará "${item}".` + (warning ? ` ${warning}` : "");

    Swal.fire({
        title: "¿Eliminar registro?",
        text: text,
        icon: "warning",
        showCancelButton: true,
        confirmButtonText: "Sí, eliminar",
        cancelButtonText: "Cancelar",
        confirmButtonColor: "#dc3545",
        cancelButtonColor: "#6c757d",
        reverseButtons: true,
        focusCancel: true,
    }).then(function (result) {
        if (result.isConfirmed) {
            form.dataset.confirmed = "true";
            form.submit();
        }
    });
});

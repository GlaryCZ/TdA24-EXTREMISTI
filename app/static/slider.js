
$(function () {
$("#slider-range").slider({
    range: true,
    min: 0,
    max: "{{max_price}}",
values: [$('#amount-min').val(), $('#amount-max').val()],
slide: function (event, ui) {
    $("#amount-min").val(ui.values[0]);
    $("#amount-max").val(ui.values[1]);
}
});
} );

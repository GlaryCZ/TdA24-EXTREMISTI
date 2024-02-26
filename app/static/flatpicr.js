config = {
    enableTime: true,
    dateFormat: "d-m-Y H",
    time_24hr: true,
    minDate: new Date().fp_incr(3),
    minuteIncrement: 60,
    altFormat: "j. F, H:00",
    altInput: true,
    "locale": 'cs',
    minTime: "8:00",
    maxTime: "19:00",
}
flatpickr("#datepick", config);

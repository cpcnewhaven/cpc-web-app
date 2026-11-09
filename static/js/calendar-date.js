// Date-only content is a local calendar day, not a UTC timestamp.
window.CPCCalendarDate = function(value) {
    return new Date(typeof value === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(value)
        ? value + 'T12:00:00' : value);
};

// Run with: node --test tests/test_content_dates_and_actions.cjs
const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const read = name => fs.readFileSync(path.join(__dirname, '../static/js', name), 'utf8');

test('date-only content keeps its calendar day in New Haven', () => {
    const previous = process.env.TZ;
    process.env.TZ = 'America/New_York';
    try {
        const context = { window: {} };
        vm.runInNewContext(read('calendar-date.js'), context);
        for (const value of ['2026-01-01', '2026-11-01', '2026-03-08']) {
            const date = context.window.CPCCalendarDate(value);
            assert.equal(date.getFullYear(), Number(value.slice(0, 4)));
            assert.equal(date.getMonth() + 1, Number(value.slice(5, 7)));
            assert.equal(date.getDate(), Number(value.slice(8, 10)));
        }
        const timestamp = '2026-11-01T02:30:00Z';
        assert.equal(+context.window.CPCCalendarDate(timestamp), +new Date(timestamp));
    } finally {
        if (previous === undefined) delete process.env.TZ;
        else process.env.TZ = previous;
    }
});

test('email actions identify distinct recipients and remove duplicate links', () => {
    const anchors = ['mailto:craig@example.org', 'mailto:jerry@example.org', 'mailto:jerry@example.org', 'javascript:alert(1)']
        .map(href => ({ getAttribute: () => href, textContent: 'Email CPC' }));
    const context = {
        window: { location: { origin: 'https://app.cpcnewhaven.org' } }, URL,
        DOMParser: class { parseFromString() { return { querySelectorAll: () => anchors }; } }
    };
    vm.runInNewContext(read('announcement-actions.js'), context);
    const actions = context.window.CPCAnnouncementActions.links({ title: 'Pastor Drop-in Office Hours' });
    assert.deepEqual(Array.from(actions, item => item.label), ['Email Craig', 'Email Jerry']);
});

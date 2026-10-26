// Makes the pill buttons filter a list.
//
// The buttons sit in an element with data-filter-group="<id of the list>".
// Each button has data-filter="all" or a kind, and each item in the list has
// data-kind. Clicking a button hides every item whose kind doesn't match.
export function setupFilters() {
  for (const group of document.querySelectorAll('[data-filter-group]')) {
    const list = document.getElementById(group.dataset.filterGroup);
    const buttons = group.querySelectorAll('button[data-filter]');

    for (const button of buttons) {
      button.addEventListener('click', () => {
        const choice = button.dataset.filter;

        for (const other of buttons) {
          other.setAttribute('aria-pressed', String(other === button));
        }

        for (const item of list.querySelectorAll('[data-kind]')) {
          item.hidden = choice !== 'all' && item.dataset.kind !== choice;
        }
      });
    }
  }
}

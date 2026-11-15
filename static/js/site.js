(() => {
    const toggle = document.querySelector('.nav-toggle');
    const navigation = document.querySelector('#primary-navigation');

    if (!toggle || !navigation) {
        return;
    }

    const closeNavigation = () => {
        toggle.setAttribute('aria-expanded', 'false');
        toggle.setAttribute('aria-label', 'Open navigation');
        navigation.classList.remove('is-open');
    };

    toggle.addEventListener('click', () => {
        const isExpanded = toggle.getAttribute('aria-expanded') === 'true';
        toggle.setAttribute('aria-expanded', String(!isExpanded));
        toggle.setAttribute(
            'aria-label',
            isExpanded ? 'Open navigation' : 'Close navigation',
        );
        navigation.classList.toggle('is-open', !isExpanded);
    });

    navigation.addEventListener('click', (event) => {
        if (event.target.closest('a')) {
            closeNavigation();
        }
    });

    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape') {
            closeNavigation();
        }
    });
})();

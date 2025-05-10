/**
 * Theme management for light/dark mode
 */
document.addEventListener('DOMContentLoaded', function() {
    const storageKey = 'preferred-theme';
    
    // Apply theme from user preference or system preference
    function applyInitialTheme() {
        // Check if user has previously set a preference
        const storedTheme = localStorage.getItem(storageKey);
        
        if (storedTheme) {
            // Apply stored preference
            setTheme(storedTheme);
        } else {
            // Apply system preference
            const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            setTheme(prefersDark ? 'dark' : 'light');
        }
        
        // Enable transitions after initial theme is applied
        setTimeout(() => {
            document.body.classList.remove('no-transition');
        }, 100);
    }
    
    // Function to set theme
    function setTheme(theme) {
        if (theme === 'dark') {
            document.documentElement.setAttribute('data-theme', 'dark');
            updateColorSchemeMeta('dark');
        } else {
            document.documentElement.removeAttribute('data-theme');
            updateColorSchemeMeta('light');
        }
    }
    
    // Update color-scheme meta tag
    function updateColorSchemeMeta(theme) {
        let metaColorScheme = document.querySelector('meta[name="color-scheme"]');
        if (!metaColorScheme) {
            metaColorScheme = document.createElement('meta');
            metaColorScheme.setAttribute('name', 'color-scheme');
            document.head.appendChild(metaColorScheme);
        }
        metaColorScheme.setAttribute('content', theme);
    }
    
    // Apply theme when page loads
    applyInitialTheme();
    
    // Listen for system preference changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
        // Only apply if the user hasn't manually set a preference
        if (!localStorage.getItem(storageKey)) {
            setTheme(e.matches ? 'dark' : 'light');
        }
    });
}); 
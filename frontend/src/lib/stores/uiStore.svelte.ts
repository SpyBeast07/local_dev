import { browser } from '$app/environment';

export const uiState = (() => {
	let isDark = $state(true);
	let isCollapsed = $state(false);

	if (browser) {
		const savedTheme = localStorage.getItem("devbeast-theme");
		if (savedTheme) {
			isDark = savedTheme === "dark";
		}
		const savedSidebar = localStorage.getItem("devbeast-sidebar");
		if (savedSidebar) {
			isCollapsed = savedSidebar === "collapsed";
		}
	}

	return {
		get isDark() { return isDark; },
		set isDark(value: boolean) {
			isDark = value;
			if (browser) localStorage.setItem("devbeast-theme", value ? "dark" : "light");
		},
		get isCollapsed() { return isCollapsed; },
		set isCollapsed(value: boolean) {
			isCollapsed = value;
			if (browser) localStorage.setItem("devbeast-sidebar", value ? "collapsed" : "expanded");
		},
		toggleTheme() {
			this.isDark = !isDark;
		},
		toggleSidebar() {
			this.isCollapsed = !isCollapsed;
		}
	};
})();

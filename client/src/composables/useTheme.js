import { ref, watch } from "vue";

const STORAGE_KEY = "inventory-theme";

const theme = ref(localStorage.getItem(STORAGE_KEY) || "light");

const applyTheme = (value) => {
  document.documentElement.setAttribute("data-theme", value);
};

// Apply initial theme immediately
applyTheme(theme.value);

watch(theme, (newTheme) => {
  localStorage.setItem(STORAGE_KEY, newTheme);
  applyTheme(newTheme);
});

export function useTheme() {
  const toggleTheme = () => {
    theme.value = theme.value === "light" ? "dark" : "light";
  };

  const setTheme = (value) => {
    theme.value = value;
  };

  return {
    theme,
    toggleTheme,
    setTheme,
  };
}

import { useTranslation } from "react-i18next";
import './LanguageSwitcher.css';

const languages = [
    { code: 'en', label: 'English', flag: '🇺🇸' },
    { code: 'es', label: 'Español', flag: '🇪🇸'}
];

const LanguageSwitcher = ({ collapsed }) => {
    const { i18n } = useTranslation();

    const changeLanguage = (langCode) => {
        i18n.changeLanguage(langCode);
    };

    return (
        <div className={`language-switcher ${collapsed ? 'collapsed' : ''}`}>
            {languages.map((lang) => (
                <button
                    key={lang.code}
                    onClick={() => changeLanguage(lang.code)}
                    className={`lang-btn ${i18n.language === lang.code ? 'active' : ''}`}
                    title={lang.label}
                >
                    <span className="lang-flag">{lang.flag}</span>
                    {!collapsed && <span className="lang-label">{lang.label}</span>}
                </button>
            ))}
        </div>
    );
};

export default LanguageSwitcher;
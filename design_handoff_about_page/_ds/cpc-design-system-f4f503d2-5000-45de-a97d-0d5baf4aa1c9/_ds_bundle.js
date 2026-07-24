/* @ds-bundle: {"format":4,"namespace":"CPCDesignSystem_f4f503","components":[{"name":"AdminButton","sourcePath":"components/admin/AdminButton.jsx"},{"name":"AdminFormField","sourcePath":"components/admin/AdminFormField.jsx"},{"name":"AdminModal","sourcePath":"components/admin/AdminModal.jsx"},{"name":"AdminPanel","sourcePath":"components/admin/AdminPanel.jsx"},{"name":"AdminStatusTag","sourcePath":"components/admin/AdminStatusTag.jsx"},{"name":"AdminTable","sourcePath":"components/admin/AdminTable.jsx"},{"name":"EventCard","sourcePath":"components/content/EventCard.jsx"},{"name":"Button","sourcePath":"components/core/Button.jsx"},{"name":"GlassCard","sourcePath":"components/core/GlassCard.jsx"},{"name":"Badge","sourcePath":"components/feedback/Badge.jsx"},{"name":"Chip","sourcePath":"components/feedback/Chip.jsx"},{"name":"FormField","sourcePath":"components/forms/FormField.jsx"},{"name":"NavBar","sourcePath":"components/navigation/NavBar.jsx"}],"sourceHashes":{"components/admin/AdminButton.jsx":"ce4e68116187","components/admin/AdminFormField.jsx":"ec789a4c2580","components/admin/AdminModal.jsx":"b91376f14d1f","components/admin/AdminPanel.jsx":"34b20f9013b2","components/admin/AdminStatusTag.jsx":"d191146d3fc9","components/admin/AdminTable.jsx":"32934ec825ec","components/content/EventCard.jsx":"ad2f0f1dad30","components/core/Button.jsx":"1ad800fc8e95","components/core/GlassCard.jsx":"23cb2ff310f3","components/feedback/Badge.jsx":"71c37313ef3f","components/feedback/Chip.jsx":"55cac0dc2506","components/forms/FormField.jsx":"72a39453e45f","components/navigation/NavBar.jsx":"520f35ce6282","ui_kits/admin-dashboard/AdminDashboardApp.jsx":"ec49cb27678d","ui_kits/admin-dashboard/AnnouncementListScreen.jsx":"450c51ce68fb","ui_kits/admin-dashboard/DashboardScreen.jsx":"284f7223dcdb","ui_kits/public-site/EventsScreen.jsx":"1223bfbc38bf","ui_kits/public-site/HomeScreen.jsx":"1be05ee94426","ui_kits/public-site/PublicSiteApp.jsx":"c7a8bed3d80a"},"inlinedExternals":[],"unexposedExports":[]} */

(() => {

const __ds_ns = (window.CPCDesignSystem_f4f503 = window.CPCDesignSystem_f4f503 || {});

const __ds_scope = {};

(__ds_ns.__errors = __ds_ns.__errors || []);

// components/admin/AdminButton.jsx
try { (() => {
const VARIANTS = {
  primary: {
    background: 'var(--admin-blue)',
    border: 'var(--admin-blue)',
    color: '#fff'
  },
  default: {
    background: 'rgba(0,50,120,0.4)',
    border: 'var(--admin-border)',
    color: 'var(--admin-text)'
  },
  success: {
    background: '#28a745',
    border: '#28a745',
    color: '#fff'
  },
  danger: {
    background: '#dc3545',
    border: '#dc3545',
    color: '#fff'
  },
  info: {
    background: '#17a2b8',
    border: '#17a2b8',
    color: '#fff'
  }
};
function AdminButton({
  variant = 'primary',
  size = 'md',
  children,
  onClick
}) {
  const v = VARIANTS[variant];
  const [hover, setHover] = React.useState(false);
  return /*#__PURE__*/React.createElement("button", {
    onClick: onClick,
    onMouseEnter: () => setHover(true),
    onMouseLeave: () => setHover(false),
    style: {
      display: 'inline-block',
      padding: size === 'sm' ? '0.35rem 0.65rem' : '0.5rem 1rem',
      fontSize: size === 'sm' ? 12 : 14,
      fontWeight: 500,
      lineHeight: 1.5,
      border: `1px solid ${v.border}`,
      borderRadius: 'var(--admin-radius-sm)',
      cursor: 'pointer',
      color: v.color,
      background: hover && variant === 'primary' ? 'var(--admin-blue-dark)' : hover && variant === 'default' ? 'rgba(0,50,120,0.6)' : v.background,
      transition: 'background 0.15s',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
    }
  }, children);
}
Object.assign(__ds_scope, { AdminButton });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/admin/AdminButton.jsx", error: String((e && e.message) || e) }); }

// components/admin/AdminFormField.jsx
try { (() => {
function AdminFormField({
  label,
  type = 'text',
  toggle = false,
  checked,
  onChange,
  placeholder
}) {
  if (toggle) {
    return /*#__PURE__*/React.createElement("div", {
      style: {
        display: 'flex',
        alignItems: 'center',
        gap: '0.5rem',
        marginBottom: '1rem'
      }
    }, /*#__PURE__*/React.createElement("input", {
      type: "checkbox",
      checked: checked,
      onChange: onChange,
      style: {
        WebkitAppearance: 'none',
        appearance: 'none',
        width: 40,
        height: 22,
        background: checked ? 'var(--admin-blue)' : 'var(--admin-panel-strong)',
        border: `1px solid ${checked ? 'var(--admin-blue)' : 'var(--admin-border)'}`,
        borderRadius: 11,
        cursor: 'pointer',
        position: 'relative'
      }
    }), /*#__PURE__*/React.createElement("label", {
      style: {
        fontSize: '0.8125rem',
        color: 'var(--admin-text)'
      }
    }, label));
  }
  return /*#__PURE__*/React.createElement("div", {
    style: {
      marginBottom: '1rem'
    }
  }, label && /*#__PURE__*/React.createElement("label", {
    style: {
      display: 'block',
      marginBottom: '0.35rem',
      fontWeight: 600,
      color: 'var(--admin-text)',
      fontSize: 14
    }
  }, label), /*#__PURE__*/React.createElement("input", {
    type: type,
    placeholder: placeholder,
    style: {
      display: 'block',
      width: '100%',
      padding: '0.5rem 0.75rem',
      fontSize: 14,
      lineHeight: 1.5,
      color: 'var(--admin-text)',
      background: 'var(--admin-panel)',
      border: '1px solid var(--admin-border)',
      borderRadius: 'var(--admin-radius-sm)',
      boxSizing: 'border-box'
    }
  }));
}
Object.assign(__ds_scope, { AdminFormField });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/admin/AdminFormField.jsx", error: String((e && e.message) || e) }); }

// components/admin/AdminModal.jsx
try { (() => {
function AdminModal({
  open,
  title,
  children,
  footer,
  onClose
}) {
  if (!open) return null;
  return /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'fixed',
      inset: 0,
      background: 'rgba(0,0,0,0.6)',
      zIndex: 1040,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: 20
    },
    onClick: onClose
  }, /*#__PURE__*/React.createElement("div", {
    onClick: e => e.stopPropagation(),
    style: {
      background: 'rgba(0,50,120,0.98)',
      border: '1px solid var(--admin-border)',
      borderRadius: 'var(--admin-radius)',
      maxWidth: 500,
      width: '100%',
      color: 'var(--admin-text)',
      boxShadow: 'var(--admin-shadow)'
    }
  }, title && /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '15px 20px',
      borderBottom: '1px solid var(--admin-border)',
      fontWeight: 600
    }
  }, title), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: 20
    }
  }, children), footer && /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '12px 20px',
      borderTop: '1px solid var(--admin-border)',
      display: 'flex',
      gap: 10,
      flexWrap: 'wrap'
    }
  }, footer)));
}
Object.assign(__ds_scope, { AdminModal });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/admin/AdminModal.jsx", error: String((e && e.message) || e) }); }

// components/admin/AdminPanel.jsx
try { (() => {
function AdminPanel({
  heading,
  children,
  style
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      background: 'rgba(19,47,76,0.4)',
      backdropFilter: 'var(--blur-sm)',
      WebkitBackdropFilter: 'var(--blur-sm)',
      border: '1px solid var(--admin-border)',
      borderRadius: 'var(--admin-radius)',
      marginBottom: '1.5rem',
      ...style
    }
  }, heading && /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '12px 15px',
      background: 'var(--admin-panel-strong)',
      borderBottom: '1px solid var(--admin-border)',
      borderRadius: 'var(--admin-radius) var(--admin-radius) 0 0',
      color: 'var(--admin-text)',
      fontWeight: 600
    }
  }, heading), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: 15,
      color: 'var(--admin-text)'
    }
  }, children));
}
Object.assign(__ds_scope, { AdminPanel });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/admin/AdminPanel.jsx", error: String((e && e.message) || e) }); }

// components/admin/AdminStatusTag.jsx
try { (() => {
const STATUS = {
  published: {
    bg: 'var(--status-success-bg)',
    text: 'var(--status-success-text)',
    border: 'var(--status-success-border)'
  },
  draft: {
    bg: 'var(--status-draft-bg)',
    text: 'var(--status-draft-text)',
    border: 'var(--status-draft-border)'
  },
  featured: {
    bg: '#0d2137',
    text: 'var(--status-featured-text)',
    border: 'var(--status-featured-border)'
  },
  banner: {
    bg: '#0d2137',
    text: 'var(--status-banner-text)',
    border: 'var(--status-banner-border)'
  },
  archived: {
    bg: '#2d2d2d',
    text: '#868e96',
    border: '#495057'
  }
};
function AdminStatusTag({
  status = 'draft',
  children
}) {
  const s = STATUS[status] || STATUS.draft;
  return /*#__PURE__*/React.createElement("span", {
    style: {
      display: 'inline-block',
      padding: '4px 10px',
      fontSize: 11,
      fontWeight: 600,
      textTransform: 'uppercase',
      letterSpacing: '0.04em',
      borderRadius: 'var(--radius-pill)',
      border: `1px solid ${s.border}`,
      background: s.bg,
      color: s.text,
      marginRight: 6,
      whiteSpace: 'nowrap'
    }
  }, children);
}
Object.assign(__ds_scope, { AdminStatusTag });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/admin/AdminStatusTag.jsx", error: String((e && e.message) || e) }); }

// components/admin/AdminTable.jsx
try { (() => {
function AdminTable({
  columns = [],
  rows = []
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      overflowX: 'auto',
      marginBottom: '1.5rem',
      background: 'rgba(19,47,76,0.4)',
      backdropFilter: 'var(--blur-sm)',
      WebkitBackdropFilter: 'var(--blur-sm)',
      border: '1px solid var(--admin-border)',
      borderRadius: 'var(--admin-radius)'
    }
  }, /*#__PURE__*/React.createElement("table", {
    style: {
      width: '100%',
      borderCollapse: 'collapse',
      color: 'var(--admin-text)',
      fontSize: 14
    }
  }, /*#__PURE__*/React.createElement("thead", {
    style: {
      background: 'var(--admin-panel-strong)'
    }
  }, /*#__PURE__*/React.createElement("tr", null, columns.map(c => /*#__PURE__*/React.createElement("th", {
    key: c,
    style: {
      padding: '14px 18px',
      textAlign: 'left',
      fontWeight: 600,
      fontSize: 12,
      textTransform: 'uppercase',
      letterSpacing: '0.04em',
      color: 'var(--admin-liquid-blue-bright)',
      borderBottom: '1px solid var(--admin-border)'
    }
  }, c)))), /*#__PURE__*/React.createElement("tbody", null, rows.map((row, i) => /*#__PURE__*/React.createElement("tr", {
    key: i,
    onMouseEnter: e => e.currentTarget.style.background = 'rgba(34,139,230,0.08)',
    onMouseLeave: e => e.currentTarget.style.background = 'transparent'
  }, columns.map(c => /*#__PURE__*/React.createElement("td", {
    key: c,
    style: {
      padding: '14px 18px',
      borderBottom: '1px solid var(--admin-border)',
      verticalAlign: 'middle'
    }
  }, row[c])))))));
}
Object.assign(__ds_scope, { AdminTable });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/admin/AdminTable.jsx", error: String((e && e.message) || e) }); }

// components/core/Button.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
const SIZES = {
  sm: {
    padding: '0.4rem 0.85rem',
    fontSize: '0.8rem'
  },
  md: {
    padding: '10px 18px',
    fontSize: '0.875rem'
  },
  lg: {
    padding: '0.875rem 1.75rem',
    fontSize: '1rem'
  }
};
function Button({
  variant = 'primary',
  size = 'md',
  children,
  onClick,
  disabled,
  style,
  ...rest
}) {
  const base = {
    display: 'inline-block',
    borderRadius: 8,
    border: 'none',
    fontWeight: 600,
    textAlign: 'center',
    cursor: disabled ? 'not-allowed' : 'pointer',
    transition: 'var(--transition-fast)',
    fontFamily: 'var(--font-primary)',
    textDecoration: 'none',
    opacity: disabled ? 0.5 : 1,
    ...SIZES[size]
  };
  const variants = {
    primary: {
      background: 'var(--cpc-blue)',
      color: '#fff'
    },
    secondary: {
      background: 'transparent',
      color: '#fff',
      border: '2px solid #fff'
    },
    glass: {
      background: 'var(--glass-white)',
      backdropFilter: 'var(--blur-md)',
      WebkitBackdropFilter: 'var(--blur-md)',
      border: '1px solid rgba(255,255,255,0.18)',
      color: 'var(--surface-text)'
    }
  };
  return /*#__PURE__*/React.createElement("button", _extends({
    onClick: onClick,
    disabled: disabled,
    style: {
      ...base,
      ...variants[variant],
      ...style
    },
    onMouseEnter: e => {
      if (disabled) return;
      if (variant === 'primary') {
        e.currentTarget.style.background = 'var(--cpc-blue-dark)';
        e.currentTarget.style.transform = 'translateY(-2px)';
      }
      if (variant === 'secondary') {
        e.currentTarget.style.background = '#fff';
        e.currentTarget.style.color = 'var(--text-primary)';
        e.currentTarget.style.transform = 'translateY(-2px)';
      }
      if (variant === 'glass') {
        e.currentTarget.style.background = 'var(--glass-bg-hover)';
        e.currentTarget.style.transform = 'translateY(-1px)';
      }
    },
    onMouseLeave: e => {
      if (disabled) return;
      Object.assign(e.currentTarget.style, variants[variant]);
      e.currentTarget.style.transform = 'none';
    }
  }, rest), children);
}
Object.assign(__ds_scope, { Button });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/Button.jsx", error: String((e && e.message) || e) }); }

// components/core/GlassCard.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
function GlassCard({
  children,
  hover = true,
  style,
  as: As = 'div',
  ...rest
}) {
  const [isHover, setHover] = React.useState(false);
  return /*#__PURE__*/React.createElement(As, _extends({
    style: {
      background: 'var(--glass-white)',
      backdropFilter: 'var(--blur-lg)',
      WebkitBackdropFilter: 'var(--blur-lg)',
      border: '1px solid rgba(255,255,255,0.18)',
      borderRadius: 'var(--radius-lg)',
      padding: 'var(--space-lg)',
      boxShadow: 'var(--shadow-soft)',
      transition: 'var(--transition-base)',
      transform: hover && isHover ? 'translateY(-4px)' : 'none',
      boxShadow: hover && isHover ? 'var(--shadow-medium)' : 'var(--shadow-soft)',
      color: 'var(--surface-text)',
      ...style
    },
    onMouseEnter: () => setHover(true),
    onMouseLeave: () => setHover(false)
  }, rest), children);
}
Object.assign(__ds_scope, { GlassCard });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/GlassCard.jsx", error: String((e && e.message) || e) }); }

// components/feedback/Badge.jsx
try { (() => {
const TYPE_COLORS = {
  event: {
    bg: 'rgba(0,122,255,0.15)',
    text: '#007AFF'
  },
  announcement: {
    bg: 'rgba(255,215,0,0.15)',
    text: '#FFD700'
  },
  ongoing: {
    bg: 'rgba(52,199,89,0.15)',
    text: '#34C759'
  },
  upcoming: {
    bg: 'rgba(255,149,0,0.15)',
    text: '#FF9500'
  }
};
function Badge({
  type = 'announcement',
  children
}) {
  const c = TYPE_COLORS[type] || {
    bg: 'rgba(255,255,255,0.1)',
    text: '#fff'
  };
  return /*#__PURE__*/React.createElement("span", {
    style: {
      display: 'inline-block',
      padding: '4px 10px',
      borderRadius: 50,
      fontSize: '0.7rem',
      fontWeight: 700,
      textTransform: 'uppercase',
      letterSpacing: '0.04em',
      background: c.bg,
      color: c.text
    }
  }, children);
}
Object.assign(__ds_scope, { Badge });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/feedback/Badge.jsx", error: String((e && e.message) || e) }); }

// components/content/EventCard.jsx
try { (() => {
function EventCard({
  category,
  title,
  when,
  location,
  description,
  actions = []
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      background: 'var(--surface-bg)',
      backdropFilter: 'var(--blur-md)',
      WebkitBackdropFilter: 'var(--blur-md)',
      border: '1px solid var(--surface-border)',
      borderRadius: 'var(--radius-lg)',
      padding: '1rem',
      transition: 'var(--transition-base)',
      color: 'var(--surface-text)'
    }
  }, category && /*#__PURE__*/React.createElement("span", {
    style: {
      display: 'inline-block',
      padding: '0.25rem 0.5rem',
      background: 'var(--surface-accent-soft)',
      borderRadius: 12,
      fontSize: '0.75rem',
      fontWeight: 600,
      marginBottom: '0.5rem'
    }
  }, category), /*#__PURE__*/React.createElement("h3", {
    style: {
      fontSize: '1.1rem',
      margin: '0.5rem 0 0.25rem',
      fontWeight: 600
    }
  }, title), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: '0.5rem',
      flexWrap: 'wrap',
      fontSize: '0.85rem',
      color: 'var(--surface-muted)',
      margin: '0.5rem 0'
    }
  }, when && /*#__PURE__*/React.createElement("span", null, when), location && /*#__PURE__*/React.createElement("span", null, "\xB7 ", location)), description && /*#__PURE__*/React.createElement("p", {
    style: {
      margin: '0.75rem 0',
      lineHeight: 1.6,
      fontSize: '0.9rem',
      opacity: 0.85
    }
  }, description), actions.length > 0 && /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: '0.5rem',
      flexWrap: 'wrap',
      marginTop: '0.75rem'
    }
  }, actions.map((a, i) => /*#__PURE__*/React.createElement(__ds_scope.Button, {
    key: i,
    variant: "glass",
    size: "sm",
    onClick: a.onClick
  }, a.label))));
}
Object.assign(__ds_scope, { EventCard });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/content/EventCard.jsx", error: String((e && e.message) || e) }); }

// components/feedback/Chip.jsx
try { (() => {
function Chip({
  active = false,
  children,
  onClick
}) {
  return /*#__PURE__*/React.createElement("button", {
    onClick: onClick,
    style: {
      padding: '0.35rem 0.7rem',
      border: `1px solid ${active ? 'var(--surface-accent)' : 'var(--surface-border)'}`,
      borderRadius: 'var(--radius-pill)',
      background: active ? 'var(--surface-accent-soft)' : 'var(--surface-bg)',
      color: active ? 'var(--surface-text)' : 'var(--surface-muted)',
      cursor: 'pointer',
      fontSize: '0.85rem',
      fontFamily: 'var(--font-primary)',
      transition: 'var(--transition-fast)'
    }
  }, children);
}
Object.assign(__ds_scope, { Chip });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/feedback/Chip.jsx", error: String((e && e.message) || e) }); }

// components/forms/FormField.jsx
try { (() => {
function FormField({
  label,
  type = 'text',
  as = 'input',
  options = [],
  value,
  onChange,
  placeholder
}) {
  const inputStyle = {
    width: '100%',
    padding: '10px 16px',
    border: '1px solid var(--surface-border)',
    borderRadius: 'var(--radius-sm)',
    fontSize: '1rem',
    fontFamily: 'var(--font-primary)',
    background: 'var(--glass-white)',
    color: 'var(--surface-text)',
    outline: 'none'
  };
  return /*#__PURE__*/React.createElement("div", {
    style: {
      marginBottom: '1rem'
    }
  }, label && /*#__PURE__*/React.createElement("label", {
    style: {
      display: 'block',
      marginBottom: '0.35rem',
      fontWeight: 600,
      color: 'var(--surface-text)',
      fontSize: '0.875rem'
    }
  }, label), as === 'select' ? /*#__PURE__*/React.createElement("select", {
    style: inputStyle,
    value: value,
    onChange: onChange
  }, options.map(o => /*#__PURE__*/React.createElement("option", {
    key: o.value,
    value: o.value
  }, o.label))) : as === 'textarea' ? /*#__PURE__*/React.createElement("textarea", {
    style: {
      ...inputStyle,
      minHeight: 100,
      resize: 'vertical'
    },
    value: value,
    onChange: onChange,
    placeholder: placeholder
  }) : /*#__PURE__*/React.createElement("input", {
    type: type,
    style: inputStyle,
    value: value,
    onChange: onChange,
    placeholder: placeholder
  }));
}
Object.assign(__ds_scope, { FormField });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/FormField.jsx", error: String((e && e.message) || e) }); }

// components/navigation/NavBar.jsx
try { (() => {
function NavBar({
  logoText = 'CPC New Haven',
  links = [],
  active
}) {
  return /*#__PURE__*/React.createElement("nav", {
    style: {
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      gap: 4,
      background: 'var(--glass-bg)',
      backdropFilter: 'var(--blur-lg)',
      WebkitBackdropFilter: 'var(--blur-lg)',
      border: '1px solid var(--glass-border)',
      borderRadius: 'var(--radius-lg)',
      boxShadow: 'var(--glass-shadow)',
      padding: '8px 16px',
      position: 'relative',
      height: 48
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'absolute',
      left: 16,
      color: 'var(--surface-text)',
      fontWeight: 700,
      fontFamily: 'var(--font-display)',
      fontSize: '0.95rem'
    }
  }, logoText), /*#__PURE__*/React.createElement("ul", {
    style: {
      display: 'flex',
      gap: 4,
      listStyle: 'none',
      margin: 0,
      padding: 0
    }
  }, links.map(l => /*#__PURE__*/React.createElement("li", {
    key: l.label
  }, /*#__PURE__*/React.createElement("a", {
    href: l.href || '#',
    style: {
      color: 'var(--surface-text)',
      fontSize: 13,
      fontWeight: 500,
      padding: '6px 10px',
      borderRadius: 6,
      textDecoration: 'none',
      background: active === l.label ? 'rgba(0,122,255,0.15)' : 'transparent'
    }
  }, l.label)))));
}
Object.assign(__ds_scope, { NavBar });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/navigation/NavBar.jsx", error: String((e && e.message) || e) }); }

// ui_kits/admin-dashboard/AdminDashboardApp.jsx
try { (() => {
function AdminDashboardApp() {
  const [screen, setScreen] = React.useState('dashboard');
  return screen === 'dashboard' ? /*#__PURE__*/React.createElement(DashboardScreen, {
    goList: () => setScreen('list')
  }) : /*#__PURE__*/React.createElement(AnnouncementListScreen, {
    goDashboard: () => setScreen('dashboard')
  });
}
ReactDOM.createRoot(document.getElementById('root')).render(/*#__PURE__*/React.createElement(AdminDashboardApp, null));
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/admin-dashboard/AdminDashboardApp.jsx", error: String((e && e.message) || e) }); }

// ui_kits/admin-dashboard/AnnouncementListScreen.jsx
try { (() => {
const {
  AdminPanel,
  AdminTable,
  AdminStatusTag,
  AdminButton,
  AdminModal,
  AdminFormField
} = window.DesignSystem_f4f503;
function AnnouncementListScreen({
  goDashboard
}) {
  const [open, setOpen] = React.useState(false);
  const rows = [{
    Title: 'Fall Retreat 2025',
    Type: 'Event',
    Status: /*#__PURE__*/React.createElement(AdminStatusTag, {
      status: "published"
    }, "Published"),
    Date: 'Oct 10',
    Actions: /*#__PURE__*/React.createElement(AdminButton, {
      size: "sm",
      variant: "default"
    }, "Edit")
  }, {
    Title: 'Christmas Eve Service',
    Type: 'Event',
    Status: /*#__PURE__*/React.createElement(AdminStatusTag, {
      status: "banner"
    }, "Banner"),
    Date: 'Dec 24',
    Actions: /*#__PURE__*/React.createElement(AdminButton, {
      size: "sm",
      variant: "default"
    }, "Edit")
  }, {
    Title: 'New Sermon Series: Luke',
    Type: 'Announcement',
    Status: /*#__PURE__*/React.createElement(AdminStatusTag, {
      status: "featured"
    }, "Featured"),
    Date: 'Sep 7',
    Actions: /*#__PURE__*/React.createElement(AdminButton, {
      size: "sm",
      variant: "default"
    }, "Edit")
  }, {
    Title: 'Summer Picnic (draft)',
    Type: 'Event',
    Status: /*#__PURE__*/React.createElement(AdminStatusTag, {
      status: "draft"
    }, "Draft"),
    Date: '—',
    Actions: /*#__PURE__*/React.createElement(AdminButton, {
      size: "sm",
      variant: "default"
    }, "Edit")
  }, {
    Title: '2024 Yearbook Archive',
    Type: 'Ongoing',
    Status: /*#__PURE__*/React.createElement(AdminStatusTag, {
      status: "archived"
    }, "Archived"),
    Date: 'Jan 2',
    Actions: /*#__PURE__*/React.createElement(AdminButton, {
      size: "sm",
      variant: "danger"
    }, "Delete")
  }];
  return /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '2.5rem',
      color: 'var(--admin-text)'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      marginBottom: 20
    }
  }, /*#__PURE__*/React.createElement("div", {
    onClick: goDashboard,
    style: {
      cursor: 'pointer',
      color: 'var(--admin-text-muted)',
      fontSize: 13
    }
  }, "\u2190 Dashboard"), /*#__PURE__*/React.createElement(AdminButton, {
    onClick: () => setOpen(true)
  }, "+ New Announcement")), /*#__PURE__*/React.createElement(AdminPanel, {
    heading: "Announcements"
  }, /*#__PURE__*/React.createElement(AdminTable, {
    columns: ['Title', 'Type', 'Status', 'Date', 'Actions'],
    rows: rows
  })), /*#__PURE__*/React.createElement(AdminModal, {
    open: open,
    title: "New Announcement",
    onClose: () => setOpen(false),
    footer: /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement(AdminButton, {
      variant: "default",
      onClick: () => setOpen(false)
    }, "Cancel"), /*#__PURE__*/React.createElement(AdminButton, null, "Save"))
  }, /*#__PURE__*/React.createElement(AdminFormField, {
    label: "Title",
    placeholder: "Announcement title"
  }), /*#__PURE__*/React.createElement(AdminFormField, {
    label: "Active",
    toggle: true,
    checked: true,
    onChange: () => {}
  })));
}
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/admin-dashboard/AnnouncementListScreen.jsx", error: String((e && e.message) || e) }); }

// ui_kits/admin-dashboard/DashboardScreen.jsx
try { (() => {
const {
  AdminButton
} = window.DesignSystem_f4f503;
function StatCard({
  n,
  label,
  color
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      background: 'var(--admin-surface-container)',
      borderRadius: 16,
      padding: '1.5rem',
      border: '1px solid var(--admin-outline-variant)',
      textAlign: 'center',
      display: 'flex',
      flexDirection: 'column',
      gap: 8
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: 'var(--font-display)',
      fontWeight: 800,
      fontSize: 30,
      color
    }
  }, n), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 9,
      fontWeight: 800,
      color: 'var(--admin-text-muted)',
      textTransform: 'uppercase',
      letterSpacing: '.15em'
    }
  }, label));
}
function WizardCard({
  title,
  desc,
  tag,
  color
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      background: 'var(--admin-surface-container)',
      borderRadius: 20,
      border: '1px solid var(--admin-outline-variant)',
      padding: '1.75rem',
      display: 'flex',
      flexDirection: 'column',
      gap: 16,
      cursor: 'pointer'
    }
  }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("h3", {
    style: {
      fontFamily: 'var(--font-display)',
      fontSize: 18,
      color: 'var(--admin-text)',
      margin: '0 0 8px'
    }
  }, title), /*#__PURE__*/React.createElement("p", {
    style: {
      fontSize: 12,
      color: 'var(--admin-text-muted)',
      margin: 0,
      lineHeight: 1.5
    }
  }, desc)), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 10,
      fontWeight: 800,
      color,
      textTransform: 'uppercase',
      letterSpacing: '.15em'
    }
  }, tag));
}
function DashboardScreen({
  goList
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '2.5rem',
      color: 'var(--admin-text)'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      background: 'var(--admin-surface-container)',
      borderRadius: 24,
      padding: '2.5rem',
      border: '1px solid var(--admin-outline-variant)',
      marginBottom: 24,
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      flexWrap: 'wrap',
      gap: 16
    }
  }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("h1", {
    style: {
      fontFamily: 'var(--font-display)',
      fontWeight: 900,
      fontSize: 32,
      color: 'var(--admin-primary)',
      margin: 0
    }
  }, "System Dashboard"), /*#__PURE__*/React.createElement("div", {
    style: {
      marginTop: 10,
      fontSize: 10,
      fontWeight: 700,
      color: 'var(--admin-text-muted)',
      textTransform: 'uppercase',
      letterSpacing: '.2em',
      background: 'var(--admin-surface-container-highest)',
      display: 'inline-block',
      padding: '6px 12px',
      borderRadius: 8,
      border: '1px solid var(--admin-outline-variant)'
    }
  }, "Monday, July 20, 2026")), /*#__PURE__*/React.createElement(AdminButton, {
    onClick: goList
  }, "Initiate New Entry")), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gridTemplateColumns: 'repeat(5,1fr)',
      gap: 14,
      marginBottom: 24
    }
  }, /*#__PURE__*/React.createElement(StatCard, {
    n: "12",
    label: "Announcements",
    color: "var(--admin-primary)"
  }), /*#__PURE__*/React.createElement(StatCard, {
    n: "248",
    label: "Sunday Sermons",
    color: "var(--admin-tertiary)"
  }), /*#__PURE__*/React.createElement(StatCard, {
    n: "86",
    label: "Podcasts",
    color: "var(--admin-secondary)"
  }), /*#__PURE__*/React.createElement(StatCard, {
    n: "1.2k",
    label: "Gallery Assets",
    color: "var(--admin-primary-dim)"
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      background: 'rgba(42,90,150,.15)',
      borderRadius: 16,
      padding: '1.5rem',
      border: '1px solid var(--admin-outline-variant)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      fontSize: 9,
      fontWeight: 800,
      color: 'var(--admin-text-muted)',
      textTransform: 'uppercase',
      letterSpacing: '.15em',
      textAlign: 'center'
    }
  }, "Audit Logs")), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gridTemplateColumns: 'repeat(3,1fr)',
      gap: 16,
      marginBottom: 24
    }
  }, /*#__PURE__*/React.createElement(WizardCard, {
    title: "Publish Sunday Sermon",
    desc: "Record a new teaching with automatic scripture mapping and platform link syndication.",
    tag: "Initialize Workflow",
    color: "var(--admin-tertiary)"
  }), /*#__PURE__*/React.createElement(WizardCard, {
    title: "Broadcast News",
    desc: "Deploy a new site-wide banner or informational update to all active channels.",
    tag: "Initialize Workflow",
    color: "var(--admin-primary)"
  }), /*#__PURE__*/React.createElement(WizardCard, {
    title: "Add Podcast Episode",
    desc: "Publish a new podcast episode with link syndication to major platforms.",
    tag: "Initialize Workflow",
    color: "var(--admin-secondary)"
  })), /*#__PURE__*/React.createElement("div", {
    onClick: goList,
    style: {
      background: 'var(--admin-surface-container)',
      borderRadius: 24,
      border: '1px solid var(--admin-outline-variant)',
      padding: '1.5rem 2rem',
      cursor: 'pointer'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: 'var(--font-display)',
      fontSize: 13,
      fontWeight: 800,
      color: 'var(--admin-primary)',
      textTransform: 'uppercase',
      letterSpacing: '.2em'
    }
  }, "Latest Content Deployed \u2192"), /*#__PURE__*/React.createElement("div", {
    style: {
      marginTop: 8,
      fontSize: 12,
      color: 'var(--admin-text-muted)'
    }
  }, "View the Announcements CRUD list")));
}
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/admin-dashboard/DashboardScreen.jsx", error: String((e && e.message) || e) }); }

// ui_kits/public-site/EventsScreen.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
const {
  NavBar,
  Chip,
  EventCard
} = window.DesignSystem_f4f503;
function EventsScreen({
  goHome
}) {
  const [cat, setCat] = React.useState('all');
  const events = [{
    category: 'Fellowship',
    title: 'Fall Retreat 2025',
    when: 'Oct 10–12',
    location: 'Camp Wightman',
    description: 'A weekend away for worship, teaching, and community.'
  }, {
    category: 'Worship',
    title: 'Advent Lessons & Carols',
    when: 'Dec 14 · 6pm',
    description: 'An evening service of scripture and song.'
  }, {
    category: 'Youth',
    title: 'Youth Group Kickoff',
    when: 'Sep 7 · 5pm',
    location: 'Fellowship Hall',
    description: 'First youth group gathering of the fall.'
  }, {
    category: 'Community',
    title: 'New Members Class',
    when: 'Sep 21 · 9am',
    description: 'Learn about membership at CPC.'
  }];
  const cats = ['all', 'Fellowship', 'Worship', 'Youth', 'Community'];
  const shown = cat === 'all' ? events : events.filter(e => e.category === cat);
  return /*#__PURE__*/React.createElement("div", {
    style: {
      color: 'var(--surface-text)',
      fontFamily: 'var(--font-primary)',
      minHeight: '100vh',
      paddingTop: 100
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'fixed',
      top: 20,
      left: '50%',
      transform: 'translateX(-50%)',
      width: 'calc(100% - 40px)',
      maxWidth: 1200,
      zIndex: 50
    }
  }, /*#__PURE__*/React.createElement(NavBar, {
    logoText: "CPC New Haven",
    active: "Events",
    links: [{
      label: 'Home'
    }, {
      label: 'Sundays'
    }, {
      label: 'Live'
    }, {
      label: 'About'
    }, {
      label: 'Events'
    }, {
      label: 'Community'
    }, {
      label: 'Give'
    }]
  })), /*#__PURE__*/React.createElement("div", {
    onClick: goHome,
    style: {
      position: 'fixed',
      top: 30,
      right: 30,
      zIndex: 60,
      cursor: 'pointer',
      color: 'var(--surface-muted)',
      fontSize: 13
    }
  }, "\u2190 Back to Home"), /*#__PURE__*/React.createElement("div", {
    style: {
      maxWidth: 1000,
      margin: '0 auto',
      padding: '20px 20px 60px'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      textAlign: 'center',
      marginBottom: 24,
      padding: '2rem 1rem',
      background: 'linear-gradient(135deg, rgba(0,40,100,.75), rgba(0,30,80,.8))',
      borderRadius: 16,
      border: '1px solid var(--surface-border)'
    }
  }, /*#__PURE__*/React.createElement("h1", {
    style: {
      fontFamily: 'var(--font-display)',
      fontSize: '1.75rem',
      margin: '0 0 4px'
    }
  }, "Events & Activities"), /*#__PURE__*/React.createElement("p", {
    style: {
      color: 'var(--surface-muted)',
      margin: 0
    }
  }, "Join us for fellowship, learning, and community events")), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 8,
      flexWrap: 'wrap',
      marginBottom: 20
    }
  }, cats.map(c => /*#__PURE__*/React.createElement(Chip, {
    key: c,
    active: cat === c,
    onClick: () => setCat(c)
  }, c === 'all' ? 'All Categories' : c))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit,minmax(280px,1fr))',
      gap: 16
    }
  }, shown.map(e => /*#__PURE__*/React.createElement(EventCard, _extends({
    key: e.title
  }, e, {
    actions: [{
      label: 'Details'
    }]
  }))))));
}
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/public-site/EventsScreen.jsx", error: String((e && e.message) || e) }); }

// ui_kits/public-site/HomeScreen.jsx
try { (() => {
const {
  Button,
  GlassCard,
  Badge,
  NavBar
} = window.DesignSystem_f4f503;
function HomeScreen({
  theme,
  setTheme,
  goEvents
}) {
  const highlights = [{
    type: 'event',
    title: 'Fall Retreat 2025 Registration Open',
    desc: 'Join us Oct 10–12 at Camp Wightman for a weekend away.'
  }, {
    type: 'announcement',
    title: 'New Sermon Series: Luke',
    desc: 'Pastor begins a new teaching series this Sunday.'
  }, {
    type: 'ongoing',
    title: 'LifeGroups Signups',
    desc: 'Find a group meeting near you this fall.'
  }];
  return /*#__PURE__*/React.createElement("div", {
    style: {
      color: 'var(--surface-text)',
      fontFamily: 'var(--font-primary)'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'fixed',
      top: 20,
      left: '50%',
      transform: 'translateX(-50%)',
      width: 'calc(100% - 40px)',
      maxWidth: 1200,
      zIndex: 50
    }
  }, /*#__PURE__*/React.createElement(NavBar, {
    logoText: "CPC New Haven",
    active: "Home",
    links: [{
      label: 'Home'
    }, {
      label: 'Sundays'
    }, {
      label: 'Live'
    }, {
      label: 'About'
    }, {
      label: 'Events',
      href: '#events'
    }, {
      label: 'Community'
    }, {
      label: 'Give'
    }]
  })), /*#__PURE__*/React.createElement("section", {
    style: {
      minHeight: 420,
      background: 'linear-gradient(to bottom, rgba(0,0,0,.75), rgba(0,0,0,.55), rgba(0,0,0,.8)), url(https://images.unsplash.com/photo-1438032005730-c779502df39b?w=1600) center/cover',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      textAlign: 'center'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      maxWidth: 700,
      padding: '80px 20px 40px'
    }
  }, /*#__PURE__*/React.createElement("h1", {
    style: {
      fontFamily: 'var(--font-display)',
      fontSize: '3rem',
      fontWeight: 800,
      color: '#fff',
      margin: '0 0 8px',
      textShadow: '0 3px 14px rgba(0,0,0,.6)'
    }
  }, "Christ Presbyterian Church"), /*#__PURE__*/React.createElement("h2", {
    style: {
      fontFamily: 'var(--font-display)',
      fontSize: '1.75rem',
      fontWeight: 700,
      color: 'rgba(255,255,255,.98)',
      margin: '0 0 16px'
    }
  }, "New Haven, CT"), /*#__PURE__*/React.createElement("p", {
    style: {
      color: 'rgba(255,255,255,.88)',
      fontSize: '1.1rem',
      margin: '0 0 24px'
    }
  }, "Everyone is truly welcomed into God's presence because there is no limit to God's grace as accomplished for us by Christ."), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 12,
      justifyContent: 'center',
      flexWrap: 'wrap'
    }
  }, /*#__PURE__*/React.createElement(Button, {
    variant: "primary"
  }, "Watch Live"), /*#__PURE__*/React.createElement(Button, {
    variant: "secondary",
    onClick: goEvents
  }, "Plan a Visit"), /*#__PURE__*/React.createElement(Button, {
    variant: "secondary"
  }, "Latest Sermon")))), /*#__PURE__*/React.createElement("section", {
    style: {
      padding: '3rem 20px',
      maxWidth: 1200,
      margin: '0 auto'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      textAlign: 'center',
      marginBottom: '2rem'
    }
  }, /*#__PURE__*/React.createElement("h2", {
    style: {
      fontFamily: 'var(--font-display)',
      fontSize: '2rem',
      fontWeight: 700,
      margin: '0 0 8px'
    }
  }, "Highlights"), /*#__PURE__*/React.createElement("p", {
    style: {
      color: 'var(--surface-muted)'
    }
  }, "Announcements and the latest from CPC")), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit,minmax(280px,1fr))',
      gap: 16
    }
  }, highlights.map(h => /*#__PURE__*/React.createElement(GlassCard, {
    key: h.title
  }, /*#__PURE__*/React.createElement(Badge, {
    type: h.type
  }, h.type), /*#__PURE__*/React.createElement("h3", {
    style: {
      fontFamily: 'var(--font-display)',
      fontSize: '1.1rem',
      margin: '10px 0 6px'
    }
  }, h.title), /*#__PURE__*/React.createElement("p", {
    style: {
      fontSize: '.9rem',
      color: 'var(--surface-muted)',
      margin: 0
    }
  }, h.desc))))), /*#__PURE__*/React.createElement("section", {
    id: "events-link",
    style: {
      padding: '2rem 20px 4rem',
      maxWidth: 900,
      margin: '0 auto',
      textAlign: 'center'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      background: 'linear-gradient(135deg, rgba(255,255,255,.8), rgba(250,250,250,.9))',
      border: '1px solid #ece7db',
      borderRadius: 18,
      padding: '2rem',
      boxShadow: '0 10px 30px rgba(0,0,0,.06)'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: 'var(--font-serif)',
      fontSize: '1.4rem',
      lineHeight: 1.6,
      color: '#2b2a27'
    }
  }, "\"Though we may be more sinful than we're even willing to imagine, we are more loved in Christ than we can ever dare to hope.\""), /*#__PURE__*/React.createElement("div", {
    style: {
      marginTop: 8,
      color: '#6b7280'
    }
  }, "You are welcome here.")), /*#__PURE__*/React.createElement("div", {
    style: {
      marginTop: 24
    }
  }, /*#__PURE__*/React.createElement(Button, {
    variant: "glass",
    onClick: goEvents
  }, "Browse Events \u2192"))));
}
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/public-site/HomeScreen.jsx", error: String((e && e.message) || e) }); }

// ui_kits/public-site/PublicSiteApp.jsx
try { (() => {
function PublicSiteApp() {
  const [screen, setScreen] = React.useState('home');
  const [theme, setTheme] = React.useState('blue');
  React.useEffect(() => {
    document.body.className = theme === 'white' ? 'theme-white' : '';
  }, [theme]);
  return /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'fixed',
      bottom: 20,
      right: 20,
      zIndex: 100,
      display: 'flex',
      gap: 8
    }
  }, /*#__PURE__*/React.createElement("button", {
    onClick: () => setTheme(theme === 'blue' ? 'white' : 'blue'),
    style: {
      padding: '8px 14px',
      borderRadius: 20,
      border: '1px solid rgba(255,255,255,.3)',
      background: 'rgba(0,0,0,.4)',
      color: '#fff',
      cursor: 'pointer',
      fontSize: 12
    }
  }, "Toggle ", theme === 'blue' ? 'Light' : 'Dark', " theme")), screen === 'home' ? /*#__PURE__*/React.createElement(HomeScreen, {
    theme: theme,
    setTheme: setTheme,
    goEvents: () => setScreen('events')
  }) : /*#__PURE__*/React.createElement(EventsScreen, {
    goHome: () => setScreen('home')
  }));
}
ReactDOM.createRoot(document.getElementById('root')).render(/*#__PURE__*/React.createElement(PublicSiteApp, null));
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/public-site/PublicSiteApp.jsx", error: String((e && e.message) || e) }); }

__ds_ns.AdminButton = __ds_scope.AdminButton;

__ds_ns.AdminFormField = __ds_scope.AdminFormField;

__ds_ns.AdminModal = __ds_scope.AdminModal;

__ds_ns.AdminPanel = __ds_scope.AdminPanel;

__ds_ns.AdminStatusTag = __ds_scope.AdminStatusTag;

__ds_ns.AdminTable = __ds_scope.AdminTable;

__ds_ns.EventCard = __ds_scope.EventCard;

__ds_ns.Button = __ds_scope.Button;

__ds_ns.GlassCard = __ds_scope.GlassCard;

__ds_ns.Badge = __ds_scope.Badge;

__ds_ns.Chip = __ds_scope.Chip;

__ds_ns.FormField = __ds_scope.FormField;

__ds_ns.NavBar = __ds_scope.NavBar;

})();

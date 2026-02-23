import React, { useState, useEffect, useRef, use } from 'react';
import { useNavigate } from 'react-router-dom';
import './LandingPage.css';


const LandingPage = () => {
    const navigate = useNavigate();
    const token = localStorage.getItem("token");
    const [ mobileMenuOpen, setMobileMenuOpen ] = useState(false);
    const [ activeFeature, setActiveFeature ] = useState(0);
    const [ visibleSections, setVisibleSections ] = useState(new Set());
    const sectionRefs = useRef({});

    useEffect(() => {
        if(token) {
            navigate("/dashboard");
        }
    }, [token, navigate])
    // Intersection Observer for scroll animations
    useEffect(() => {
        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        setVisibleSections((prev) => new Set([...prev, entry.target.id]));
                    }
                });
            },
            { threshold: 0.15 }
        );

        const sections = document.querySelectorAll(".animate-section");
        sections.forEach((section) => observer.observe(section));

        return () => observer.disconnect();
    }, []);

    // Auto-rotate features
    useEffect(() => {
        const interval = setInterval(() => {
            setActiveFeature((prev) => (prev + 1) % features.length);
        }, 4000);
        return () => clearInterval(interval);
    }, []);

    const features = [
        {
            icon: "📊",
            title: "Smart Dashboard",
            description: "Get a complete bird's-eye view of your finances. Interactive charts, spending trends, and real-time summaries all in one place.",
            color: "#3b82f6",
            preview: {
                title: "Dashboard",
                stats: [
                    { label: "Balance", value: "\$12,450", change: "+8.2%" },
                    { label: "This Month", value: "\$3,200", change: "-12%" },
                ],
            },
        },
        {
            icon: "💳",
            title: "Transaction Tracking",
            description: "Log every expense and income with smart categorization. Search, filter, and sort your financial history effortlessly.",
            color: "#22c55e",
            preview: {
                title: "Transactions",
                items: [
                    { name: "Grocery Store", amount: "-\$85.40", cat: "Food" },
                    { name: "Freelance Payment", amount: "+\$2,500", cat: "Income" },
                    { name: "Netflix", amount: "-\$15.99", cat: "Entertainment" },
                ],
            },
        },
        {
            icon: "🎯",
            title: "Budget Goals",
            description: "Set monthly budgets by category and track progress in real-time. Get alerts when you're approaching your limits.",
            color: "#f59e0b",
            preview: {
                title: "Budgets",
                budgets: [
                    { name: "Food & Dining", used: 75, total: "\$400" },
                    { name: "Entertainment", used: 45, total: "\$200" },
                    { name: "Transportation", used: 90, total: "\$150" },
                ],
            },
        },
        {
            icon: "🔄",
            title: "Subscription Manager",
            description: "Never lose track of recurring payments. Monitor all your subscriptions, see upcoming charges, and indentify savings opportunities.",
            color: "#8b5cf6",
            preview: {
                title: "Subscriptions",
                subs: [
                    { name: "Spotify", amount: "\$9.99/mo", status: "active" },
                    { name: "AWS", amount: "\$45.00/mo", status: "active" },
                    { name: "Gym", amount: "\$30.00/mo", status: "paused" },
                ],
            },
        },
        {
            icon: "💰",
            title: "Income Tracking",
            description: "Monitor multiple income sources with period tracking. Visualize your earning patterns and plan ahead with confidence.",
            color: "#ec4899",
            preview: {
                title: "Income",
                sources: [
                    { name: "Salary", amount: "\$5,000" },
                    { name: "Freelance", amount: "\$1,200" },
                    { name: "Investments", amount: "\$350" },
                ],
            },
        },
        {
            icon: "🤝",
            title: "Shared Budgets",
            description: "Split expenses with roommates, family, or friends. Track who owes what and settle up with ease. Perfect for shared living.",
            color: "#06b6d4",
            preview: {
                title: "Shared Budget",
                members: ["You", "Mike", "Sarah"],
                spent: "\$1,450 of \$2,000",
            },
        },
    ];

    const testimonials = [
        {
            text: "I finally know where my money goes each month. The dashboard alone is worth it - I've saved over \$300 by catching subscriptions I forgot about.",
            name: "Sarah Johnson",
            role: "Freelance Designer",
            avatar: "SJ",
            color: "#3b82f6",
        },
        {
            text: "The shared budgets feature is a game-changer for our apartment. No more awkward money conversations - everything is tracked and transparent.",
            name: "Michael Chen",
            role: "Software Engineer",
            avatar: "MC",
            color: "#22c55e",
        },
        {
            text: "As a small business owner, tracking personal ad business expenses was a nightmare. This app makes it simple and even fun.",
            name: "Emily Rodriguez",
            role: "Business Owner",
            avatar: "ER",
            color: "#f59e0b",
        },
        {
            text: "The budget alerts saved me from overspending multiple times. It's like having a financial advisor in your pocket.",
            name: "David Park",
            role: "Marketing Manager",
            avatar: "DP",
            color: "#8b5cf6",
        },
    ];

    const stats = [
        { value: "50K+", label: "Active Users", icon: "👥" },
        { value: "\$12M+", label: "Tracked Monthly", icon: "💰" },
        { value: "4.9", label: "User Rating", icon: "⭐"},
        { value: "99.9%", label: "Uptime", icon: "🔒" },
    ];

    const faqs = [
        {
            q: "Is my financial data secure?",
            a: "Absolutetly. We use a bank-level 256-bit encryption. Your data is never share with third parties, and you can export or delete it anytime.",
        },
        {
            q: "Can I share budgets with friends who don't have an account?",
            a: "They'll need to create a free account to participate in shared budgets. It only takes 30 seconds to sign up!",
        },
        {
            q: "How does the expense splitting work?",
            a: "You can split expenses equally, by percentage or with custom amount. The app automatically calculates who owes whom and tracks settlements.",
        },
        {
            q: "Can I export my data?",
            a: "Yes! You can export all your transactions, budgets, an reports to CSV or PDF format at any time.",
        },
        {
            q: "Is there a mobile app?",
            a: "Our web app is fully responsive and works great on any device. Native iOS and Android apps are coming soon!",
        },
        {
            q: "What happens if I cancel?",
            a: "You can use the free plan forever. If you cancel a paid plan, you'll keep access until the end of your billing period. Your data is always yours.",
        },
    ];

    const getFeaturePreview = (feature) => {
        const p = feature.preview;

        if (p.stats) {
            return (
                <div className="lp-preview-dashboard">
                    <div className="lp-preview-title-bar">
                        <div className="lp-preview-dots">
                            <span style={{ background: "#ef4444" }}></span>
                            <span style={{ background: "#f59e0b" }}></span>
                            <span style={{ background: "#22c55e" }}></span>
                        </div>
                        <span className="lp-preview-tab">{p.title}</span>
                    </div>
                    <div className="lp-preview-stats">
                        {p.stats.map((stat, i) => (
                            <div key={i} className="lp-preview-stat">
                                <span className="lp-ps-label">{stat.label}</span>
                                <span className="lp-ps-value">{stat.value}</span>
                                <span className={`lp-ps-change ${stat.change.startsWith("+") ? "pos" : "neg"}`}>
                                    {stat.change}
                                </span>
                            </div>
                        ))}
                    </div>
                    <div className="lp-preview-chart">
                        {[40, 65, 45, 80, 55, 90, 70].map((h, i) => (
                            <div
                                key={i}
                                className="lp-chart-bar"
                                style={{
                                    height: `${h}%`,
                                    backgroundColor: i === 5 ? feature.color : "#333",
                                    animationDelay: `${i * 0.1}s`,
                                }}
                            />
                        ))}
                    </div>
                </div>
            );
        }

        if (p.items) {
            return (
                <div className="lp-preview-list-view">
                    <div className="lp-preview-title-bar">
                        <div className="lp-preview-dots">
                            <span style={{ background: "#ef4444" }}></span>
                            <span style={{ background: "#f59e0b" }}></span>
                            <span style={{ background: "#22c55e" }}></span>
                        </div>
                        <span className="lp-preview-tab">{p.title}</span>
                    </div>
                    <div className="lp-preview-items">
                        {p.items.map((item, i) => (
                            <div key={i} className="lp-preview-item">
                                <div className="lp-pi-left">
                                    <span className="lp-pi-name">{item.name}</span>
                                    <span className="lp-pi-cat">{item.cat}</span>
                                </div>
                                <span className={`lp-pi-amount ${item.amount.startsWith("+") ? "pos" : "neg"}`}>
                                    {item.amount}
                                </span>
                            </div>
                        ))}
                    </div>
                </div>
            );
        }

        if (p.budgets) {
            (
                <div className="lp-preview-budgets-view">
                    <div className="lp-preview-title-bar">
                        <div className="lp-preview-dots">
                            <span style={{ background: "#ef4444" }}></span>
                            <span style={{ background: "#f59e0b" }}></span>
                            <span style={{ background: "#22c55e" }}></span>
                        </div>
                        <span className="lp-preview-tab">{p.title}</span>
                    </div>
                    <div className="lp-preview-budget-items">
                        {p.budgets.map((b, i) => (
                            <div key={i} className="lp-pb-item">
                                <div className="lp-pb-header">
                                    <span className="lp-pb-name">{b.name}</span>
                                    <span className="lp-pb-total">{b.total}</span>
                                </div>
                                <div className="lp-pb-bar">
                                    <div
                                        className="lp-pb-fill"
                                        style={{
                                            width: `${b.used}%`,
                                            backgroundColor: 
                                                b.used >= 90 ? "#ef4444" : b.used >= 70 ? "#f59e0b" : "#22c55e",
                                        }}
                                    />
                                </div>
                                <span className="lp-pb-percent">{b.used}</span>
                            </div>
                        ))}
                    </div>
                </div>
            );
        }

        if (p.subs) {
            return (
                <div className="lp-preview-subs-view">
                    <div className="lp-preview-title-bar">
                        <div className="lp-preview-dots">
                            <span style={{ background: "#ef4444" }}></span>
                            <span style={{ background: "#f59e0b" }}></span>
                            <span style={{ background: "#22c55e" }}></span>
                        </div>
                        <span className="lp-preview-tab">{p.title}</span>
                    </div>
                    <div className="lp-preview-sub-items">
                        {p.subs.map((sub, i) => (
                            <div key={i} className="lp-psub-item">
                                <span className="lp-psub-name">{sub.name}</span>
                                <span className="lp-psub-amount">{sub.amount}</span>
                                <span className={`lp-psub-status ${sub.status}`}>{sub.status}</span>
                            </div>
                        ))}
                    </div>
                </div>
            );
        }

        if (p.sources) {
            return (
                <div className="lp-preview-income-view">
                    <div className="lp-preview-title-bar">
                        <div className="lp-preview-dots">
                            <span style={{ background: "#ef4444" }}></span>
                            <span style={{ background: "#f59e0b" }}></span>
                            <span style={{ background: "#22c55e" }}></span>
                        </div>
                        <span className="lp-preview-tab">{p.title}</span>
                    </div>
                    <div className="lp-preview-source-items">
                        {p.sources.map((src, i) => (
                            <div key={i} className="lp-psrc-item">
                                <span className="lp-psrc-name">{src.name}</span>
                                <span className="lp-psrc-amount">{src.amount}</span>
                            </div>
                        ))}
                        <div className="lp-psrc-total">
                            <span>Total</span>
                            <span>\$6,550</span>
                        </div>
                    </div>
                </div>
            );
        }

        if (p.members) {
            return (
                <div className="lp-preview-shared-view">
                    <div className="lp-preview-title-bar">
                        <div className="lp-preview-dots">
                            <span style={{ background: "#ef4444" }}></span>
                            <span style={{ background: "#f59e0b" }}></span>
                            <span style={{ background: "#22c55e" }}></span>
                        </div>
                        <span className="lp-preview-tab">{p.title}</span>
                    </div>
                    <div className="lp-preview-shared-content">
                        <div className="lp-psh-members">
                            {p.members.map((m, i) => (
                                <div key={i} className="lp-psh-avatar">
                                    {m[0]}
                                </div>
                            ))}
                        </div>
                        <div className="lp-psh-progress">
                            <div className="lp-psh-bar">
                                <div className="lp-psh-fill" style={{ width: "72%" }} />
                            </div>
                            <span className="lp-psh-text">{p.spent}</span>
                        </div>
                    </div>
                </div>
            );
        }

        return null;

    };

    return (
        <div className="landing-page">
            {/* Navigation */}
            <nav className="lp-nav">
                <div className="lp-nav-container">
                    <a href="/" className="lp-logo">
                        <span className="lp-logo-icon">💰</span>
                        <span className="lp-logo-text">Money Manager</span>
                    </a>

                    <ul className="lp-nav-links">
                        <li><a href="#features">Features</a></li>
                        <li><a href="#how-it-works">How It Works</a></li>
                        <li><a href="#testimonials">Reviews</a></li>
                        <li><a href="#faq">FAQ</a></li>
                    </ul>

                    <div className="lp-nav-actions">
                        <button className="lp-btn-ghost" onClick={() => navigate("/login")}>
                            Log In
                        </button>
                        <button className="lp-btn-primary" onClick={() => navigate("/register")}>
                            Get Started Free
                        </button>
                    </div>

                    <button
                        className="lp-mobile-menu-btn"
                        onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                    >
                        {mobileMenuOpen ? "✕" : "☰"}
                    </button>
                </div>

                {/* Mobile Menu */}
                {mobileMenuOpen && (
                    <div className="lp-mobile-menu">
                        <a href="#features" onClick={() => setMobileMenuOpen(false)}>Features</a>
                        <a href="#how-it-works" onClick={() => setMobileMenuOpen(false)}>How It Works</a>
                        <a href="#testimonials" onClick={() => setMobileMenuOpen(false)}>Reviews</a>
                        <a href="#faq" onClick={() => setMobileMenuOpen(false)}>FAQ</a>
                        <div className="lp-mobile-actions">
                            <button className="lp-btn-ghost" onClick={() => navigate("/login")}>Log In</button>
                            <button className="lp-btn-primary" onClick={() => navigate("/register")}>Sign Up</button>
                        </div>
                    </div>
                )}
            </nav>

            {/* Hero */}
            <section className="lp-hero">
                <div className="lp-hero-bg">
                    <div className="lp-hero-glow glow-1" />
                    <div className="lp-hero-glow glow-2" />
                </div>
                <div className="lp-hero-content">
                    <div className="lp-hero-left">
                        <div className="lp-hero-badge">
                            <span className="lp-badge-dot"/>
                                New: Shared Budgets with Friends 🤝
                        </div>
                        <h1 className="lp-hero-title">
                            Your Money,{" "}
                            <span className="lp-gradient-text">Your Rules,</span>{" "}
                            Your Future.
                        </h1>
                        <p className="lp-hero-subtitle">
                            Track expenses, manage budgets, split costs with friends,
                            and take control of your financial life - all in one 
                            beautifully simple app.
                        </p>
                        <div className="lp-hero-actions">
                            <button
                                className="lp-btn-primary lp-btn-lg"
                                onClick={() => navigate("/register")}
                            >
                                Start For Free
                                <span className="lp-btn-arrow">→</span>
                            </button>
                            <a href="#features" className="lp-btn-outline lp-btn-lg">
                                See Features
                            </a>
                        </div>
                        <div className="lp-hero-trust">
                            <div className="lp-trust-avatars">
                                {["#3b82f6", "#22c55e", "#f59e0b", "#ec4899"].map((c, i) => (
                                    <div
                                        key={i}
                                        className="lp-trust-avatar"
                                        style={{ backgroundColor: c }}
                                    />
                                ))}
                            </div>
                            <span>Joined by <strong>50,000+</strong> users this month</span>
                        </div>
                    </div>

                    <div className="lp-hero-right">
                        <div className="lp-hero-preview">
                            <div className="lp-hp-sidebar">
                                <div className="lp-hp-logo">💰</div>
                                    {["📊", "💳", "🎯", "🔄", "💰", "👥", "🤝"].map((icon, i) => (
                                        <div key={i} className={`lp-hp-nav-item ${i === 0 ? "active" : ""}`}>
                                            {icon}
                                        </div>
                                    ))}
                            </div>

                            <div clasName="lp-hp-main">
                                <div className="lp-hp-header">
                                    <span>Dashboard</span>
                                    <div className="lp-hp-user">JD</div>
                                </div>
                                <div className="lp-hp-cards">
                                    <div className="lp-hp-card">
                                        <span className="lp-hp-card-label">Balance</span>
                                        <span className="lp-hp-card-value">\$24,562</span>
                                    </div>
                                    <div className="lp-hp-card">
                                        <span className="lp-hp-card-label">This Month</span>
                                        <span className="lp-hp-card-value">-\$3,218</span>
                                    </div>
                                </div>
                                <div className="lp-hp-chart">
                                    {[35, 55, 40, 70, 50, 85, 60, 75, 90, 65, 80, 70].map((h, i) => (
                                        <div
                                            key={i}
                                            className="lp-hp-bar"
                                            style={{ height: `${h}%` }}
                                        />
                                    ))}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* STATS */}
            <section className="lp-stats">
                <div className="lp-stats-container">
                    {stats.map((stat, i ) => (
                        <div key={i} className="lp-stat-item">
                            <span className="lp-stat-icon">{stat.icon}</span>
                            <span className="lp-stat-value">{stat.value}</span>
                            <span className="lp-stat-label">{stat.label}</span>
                        </div>
                    ))}
                </div>
            </section>

            {/* FEATURES */}
            <section
                id="features"
                className={`lp-features animate-section ${visibleSections.has("features") ? "visible" : ""}`}
            >
                <div className="lp-section-header">
                    <span className="lp-section-badge">Features</span>
                    <h2>Everythin you need to master your money</h2>
                    <p>Powerful yet simple tools designed for real people, not accountants.</p>
                </div>

                <div className="lp-features-showcase">
                    {/* Feature Tabs */}
                    <div className="lp-feature-tabs">
                        {features.map((feature, i) => (
                            <button
                                key={i}
                                className={`lp-feature-tab ${activeFeature === i ? "active" : ""}`}
                                onClick={() => setActiveFeature(i)}
                                style={{
                                    borderColor: activeFeature === i ? feature.color : "transparent",
                                }}
                            >
                                <span className="lp-ft-icon">{feature.icon}</span>
                                <div className="lp-ft-text">
                                    <span className="lp-ft-title">{feature.title}</span>
                                    <span className="lp-ft-desc">{feature.description}</span>
                                </div>
                            </button>
                        ))}
                    </div>

                    {/* Feature Preview */}
                    <div className="lp-feature-preview">
                        <div
                            className="lp-fp-glow"
                            style={{ backgroundColor: features[activeFeature].color }}
                        />
                        {getFeaturePreview(features[activeFeature])}
                    </div>
                </div>
            </section>

            {/* HOW IT WORKS */}
            <section
                id="how-it-works"
                className={`lp-how-it-works animate-section ${visibleSections.has("how-it-works") ? "visible" : ""}`}
            >
                <div className="lp-section-header">
                    <span className="lp-section-badge">How It Works</span>
                    <h2>Get started in minutes, not hours</h2>
                </div>

                <div className="lp-steps">
                    {[
                        {
                            num: "01",
                            title: "Create Your Account",
                            desc: "Sign up for free in under 30 seconds. No credit card, no commitment.",
                            icon: "🚀",
                        },
                        {
                            num: "02",
                            title: "Set Up Your Finances",
                            desc: "Add your income sources, set budgets, and log you subscriptions.",
                            icon: "⚙️",
                        },
                        {
                            num: "03",
                            title: "Invite Friends",
                            desc: "Connect with roommates, partners, or family for shared budgets.",
                            icon: "👥",
                        },
                        {
                            num: "04",
                            title: "Track & Grow",
                            desc: "Watch your financial health improve with insights and smart alerts.",
                            icon: "📈",
                        },
                    ].map((step, i) => (
                        <div key={i} className="lp-step">
                            <div className="lp-step-number">{step.num}</div>
                            <div className="lp-step-icon">{step.icon}</div>
                            <h3>{step.title}</h3>
                            <p>{step.desc}</p>
                        </div>
                    ))}
                </div>
            </section>

            {/* SHARED BUDGETS HIGHLIGHT */}
            <section
                className={`lp-shared-highlight animate-section ${visibleSections.has("shared-highlight") ? "visible" : ""}`}
            >
                <div className="lp-sh-content">
                    <div className="lp-sh-text">
                        <span className="lp-section-badge">New Features</span>
                        <h2>Split expenses without the awkwardness</h2>
                        <p>
                            Whether it's rent with rommates, a vacation with friends,
                            or family groceries - shared budgets make splitting costs
                            transparent and painless.
                        </p>
                        <ul className="lp-sh-features">
                            <li><span className="lp-check">✓</span> Create shared budgets with friends</li>
                            <li><span className="lp-check">✓</span> Split expenses equally, by percentage or custom</li>
                            <li><span className="lp-check">✓</span> Real-time balance tracking for all members</li>
                            <li><span className="lp-check">✓</span> Simple "Settle Up" to clear debts</li>
                            <li><span className="lp-check">✓</span> Activity notifications for every change</li>
                        </ul>
                        <button className="lp-btn-primary lp-btn-lg" onClick={() => navigate("/register")}>
                            Try Shared Budgets Free
                            <span className="lp-btn-arrow">→</span>
                        </button>
                    </div>
                    <div className="lp-sh-visual">
                        <div className="lp-sh-card">
                            <h4>🏠 Apartment Expenses</h4>
                            <div className="lp-sh-progress-bar">
                                <div className="lp-sh-fill" style={{ width: "68%" }} />
                            </div>
                            <span className="lp-sh-progress-text">\$1,360 of \$2,000 (68%)</span>
                            <div className="lp-sh-members">
                                <div className="lp-sh-member">
                                    <div className="lp-sh-avatar" style={{ background: "#3b82f6" }}>Y</div>
                                    <div>
                                        <span className="lp-sh-name">You</span>
                                        <span className="lp-sh-balance positive">+\$45.00</span>
                                    </div>
                                </div>
                                <div className="lp-sh-member">
                                    <div className="lp-sh-avatar" style={{ background: "#22c55e" }}>M</div>
                                    <div>
                                        <span className="lp-sh-name">Mike</span>
                                        <span className="lp-sh-balance negative">-\$32.50</span>
                                    </div>
                                </div>
                                <div className="lp-sh-member">
                                    <div className="lp-sh-avatar" style={{ background: "#f59e0b"}}>S</div>
                                    <div>
                                        <span className="lp-sh-name">Sarah</span>
                                        <span className="lp-sh-balance negative">-\$12.50</span>
                                    </div>
                                </div>
                            </div>
                            <div className="lp-sh-settle">
                                <span>Mike owes you \$32.50</span>
                                <button>Settle Up</button>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* TESTIMONIALS */}
            <section
                id="testimonials"
                className={`lp-testimonials animate-section ${visibleSections.has("testimonials") ? "visible" : ""}`}
            >
                <div className="lp-section-header">
                    <span className="lp-section-badge">Testimonials</span>
                    <h2>Loved by thousands of users</h2>
                </div>
                <div className="lp-testimonials-grid">
                    {testimonials.map((t, i) => (
                        <div key={i} className="lp-testimonial-card">
                            <div className="lp-tc-stars">★★★★★</div>
                                <p className="lp-tc-text">"{t.text}"</p>
                            <div className="lp-tc-author">
                                <div className="lp-tc-avatar" style={{ backgroundColor: t.color }}>
                                    {t.avatar}
                                </div>
                                <div>
                                    <span className="lp-tc-name">{t.name}</span>
                                    <span className="lp-tc-role">{t.role}</span>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </section>

            {/* FAQ */}
            <section
                id="faq"
                className={`lp-faq animate-section ${visibleSections.has("faq") ? "visible" : ""}`}
            >
                <div className="lp-section-header">
                    <span className="lp-section-badge">FAQ</span>
                    <h2>Frequently asked questions</h2>
                </div>
                <div className="lp-faq-list">
                    {faqs.map((faq, i) => (
                        <details key={i} className="lp-faq-item">
                            <summary>{faq.q}</summary>
                            <p>{faq.a}</p>
                        </details>
                    ))}
                </div>
            </section>

            {/* CTA */}
            <section className="lp-cta">
                <div className="lp-cta-grow" />
                <div className="lp-cta-content">
                    <h2>Ready to take control of your finances?</h2>
                    <p>Join 50,000+ users who area already managing their money smarter.</p>
                    <div className="lp-cta-actions">
                        <button className="lp-btn-primary lp-btn-lg" onClick={() => navigate("/register")}>
                            Create Free Account
                            <span className="lp-btn-arrow">→</span>
                        </button>
                    </div>
                    <span className="lp-cta-note">
                         ✓ Free forever plan &nbsp;&nbsp; ✓ No credit card required &nbsp;&nbsp; ✓ Cancel anytime
                    </span>
                </div>
            </section>

            {/* FOOTER */}
            <footer className="lp-footer">
                <div className="lp-footer-container">
                    <div className="lp-footer-brand">
                        <a href="/" className="lp-logo">
                            <span className="lp-logo-icon">💰</span>
                            <span className="lp-logo-text">Money Manager</span>
                        </a>
                        <p>Your personal finance companion for a brighter financial future.</p>
                    </div>
                    <div className="lp-footer-links">
                        <div className="lp-footer-col">
                            <h4>Product</h4>
                            <a href="#features">Features</a>
                            <a href="#how-it-works">How It Works</a>
                            <a href="#testimonials">Reviews</a>
                            <a href="#faq">FAQ</a>
                        </div>
                        <div className="lp-footer-col">
                            <h4>Company</h4>
                            <a href="#">About Us</a>
                            <a href="#">Blog</a>
                            <a href="#">Careers</a>
                            <a href="#">Contact</a>
                        </div>
                        <div className="lp-footer-col">
                            <h4>Legal</h4>
                            <a href="#">Privace Policy</a>
                            <a href="#">Terms of Service</a>
                            <a href="#">Cookie Policy</a>
                        </div>
                    </div>
                </div>
                <div className="lp-footer-bottom">
                    <span>© {new Date().getFullYear()} Money Manager. All rights reserved.</span>
                    <div className="lp-social-links">
                        <a href="#">𝕏</a>
                        <a href="#">in</a>
                        <a href="#">⌘</a>
                    </div>
                </div>
            </footer>
        </div>
    );
};

export default LandingPage;
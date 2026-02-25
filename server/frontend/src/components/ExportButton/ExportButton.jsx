import React, { useState, useRef, useEffect } from 'react';
import { exportToCSV, exportToPDF } from '../../utils/export';
import "./ExportButton.css";

const ExportButton = ({
    data = [],
    columns = [],
    title = "Export",
    subtitle = "",
    filename = "export",
    summary = [],
    orientation = "portrait",
    onExport,
}) => {
    const [ open, setOpen ] = useState(false);
    const [ exporting, setExporting ] = useState(null);
    const dropdownRef = useRef(null);

    // Close dropdown on outside click
    useEffect(() => {
        const handleClickOutside = (e) => {
            if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
                setOpen(false);
            }
        };
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    const handleExport = async (format) => {
        if (!data || data.length === 0) {
            onExport?.("error", "No data to export");
            return;
        }

        setExporting(format);

        try {
            let success = false;

            if (format === "csv") {
                success = exportToCSV(data, columns, filename);
            } else if (format === "pdf") {
                success = exportToPDF({
                    title,
                    subtitle,
                    data,
                    columns,
                    summary,
                    filename,
                    orientation,
                });
            }

            if (success) {
                onExport?.("success", `Exported as ${format.toUpperCase()}`);
            } else {
                onExport?.("error", "Export failed - no data");
            }
        } catch (error) {
            console.error("Export error:", error);
            onExport?.("error", "Export failed");
        } finally {
            setExporting(null);
            setOpen(false);
        }
    };

    return (
        <div className="export-btn-wrapper" ref={dropdownRef}>
            <button 
                className="export-btn"
                onClick={() => setOpen(!open)}
                disabled={!data || data.length === 0}
            >
                📥 Export
                <span className={`export-chevron ${open ? "open" : ""}`}>
                    ▾
                </span>
            </button>

            {open && (
                <div className="export-dropdown">
                    <button
                        className="export-option"
                        onClick={() => handleExport("csv")}
                        disabled={exporting === "csv"}
                    >
                        <span className="export-option-icon">📄</span>
                        <div className="export-option-text">
                            <span className="export-option-title">
                                {exporting === "csv"
                                    ? "Exporting..."
                                    : "Export as CSV"}
                            </span>
                            <span className="export-option-desc">
                                Spreadsheet-compatible format
                            </span>
                        </div>
                    </button>

                    <button
                        className="export-option"
                        onClick={() => handleExport("pdf")}
                        disabled={exporting === "pdf"}
                    >
                        <span className="export-option-icon">📑</span>
                        <div className="export-option-text">
                            <span className="export-option-title">
                                {exporting === "pdf"
                                    ? "Exporting..."
                                    : "Export as PDF"}
                            </span>
                            <span className="export-option-desc">
                                Formatted report with styling
                            </span>
                        </div>
                    </button>
                </div>
            )}
        </div>
    );
};

export default ExportButton;
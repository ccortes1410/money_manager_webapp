import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';

// CSV EXPORT

// Convert an array of objects to CSV string
function objectsToCSV(data, columns) {
    if (!data || data.length === 0) return "";

    // Header row
    const header = columns.map((col) => `"${col.label}"`).join(",");

    // Data rows
    const rows = data.map((item) => {
        return columns
            .map((col) => {
                let value = col.accesor(item);
                if (value === null || value === undefined) value = "";
                // Escape quotes and wrap in quotes
                value = String(value).replace(/"/g, '""');
                return `"${value}"`;
            })
            .join(",");
    });

    return [header, ...rows].join("\n");
}

// Download a string as a file
function downloadFile(content, filename, mimeType) {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
}

// Export data to CSV

/**
 * 
 * @param {*} data - Array of objects
 * @param {*} columns - columns - [{ label: "Name", accesor: (item) => item.name }]
 * @param {*} filename - File name without extension
 */

export function exportToCSV(data, columns, filename = "export") {
    const csv = objectsToCSV(data, columns);
    if (!csv) return false;
    downloadFile(csv, `${filename}.csv`, "text/csv;charset-utf-8;");
    return true;
}


// PDF EXPORT

/**
 * Export data to PDF
 * @param {Object} options
 * @param {string} options.title - Document title
 * @param {string} options.subtitle - Optional subtitle (e.g., date range)
 * @param {Array} options.data - Array of objects
 * @param {Array} options.columns - [{ label: "Name", accesor: (item) => item.name }]
 * @param {Array} options.summary - Optional summary rows [{ label: "Total", value: "\$500" }]
 * @param {string} options.filename - File name without extension
 * @param {string} options.orientation - "portrait" or "landscape"
 */ 
export function exportToPDF({
    title = "Export",
    subtitle = "",
    data = [],
    columns = [],
    summary = [],
    filename = "export",
    orientation = "portrait",
}) {
    if (!data || data.length === 0) return false;

    const doc = new jsPDF({ orientation, unit: "mm", format: "a4" });
    const pageWidth = doc.internal.pageSize.getWidth();

    // Colors matching the app theme
    const primaryColor = [59, 130, 246]; // #3b82f6
    const darkBg = [15, 15, 15]; // #0f0f0f
    const cardBg = [26, 26, 26]; // #1a1a1a;
    const headerBg = [37, 37, 37]; // #252525;
    const textWhite = [255, 255, 255];
    const textMuted = [136, 136, 136]; // #888
    const greenColor = [34, 197, 94]; // #22c55e

    // Background
    doc.setFillColor(...primaryColor);
    doc.rect(0, 0, pageWidth, 2, "F");

    // Logo / App name
    doc.setTextColor(...textMuted);
    doc.setFontSize(16);
    doc.text("Money Manager", 14, 12);

    // Title
    doc.setTextColor(...textWhite);
    doc.setFontSize(20);
    doc.setFont(undefined, "bold");
    doc.text(title, 14, 24);

    // Subtitle
    let yPos = 30;
    if (subtitle) {
        doc.setTextColor(...textMuted);
        doc.setFontSize(10);
        doc.setFont(undefined, "normal");
        doc.text(subtitle, 14, yPos);
        yPos += 4;
    }

    // Generated date
    doc.setTextColor(...textMuted);
    doc.setFontSize(8);
    doc.text(
        `Generated: ${new Date().toLocaleDateString("en-US", {
            year: "numeric",
            month: "long",
            day: "numeric",
            hour: "2-digit",
            minute: "2-digit",
        })}`,
        14,
        yPos + 4
    );
    yPos += 10;

    // Summary cards (if provided)
    if (summary.length > 0) {
        const cardWidth = (pageWidth - 28 - (summary.length - 1) * 4) / summary.length;
        const cardHeight = 18;

        summary.forEach((item, i) => {
            const x = 14 + i * (cardWidth + 4);

            // Card background
            doc.setFillColor(...cardBg);
            doc.roundedRect(x, yPos, cardWidth, cardHeight, 2, 2, "F");

            // Card border-left accent
            if (item.color) {
                doc.setFillColor(...item.color);
                doc.rect(x, yPos, 1.5, cardHeight, "F");
            }

            // Label
            doc.setTextColor(...textMuted);
            doc.setFontSize(7);
            doc.setFont(undefined, "normal");
            doc.text(item.label.toUpperCase(), x + 5, yPos + 6);

            // Value
            doc.setTextColor(...textWhite);
            doc.setFontSize(12);
            doc.setFont(undefined, "bold");
            doc.text(String(item.value), x + 5, yPos + 14);
        });

        yPos += cardHeight + 6;
    }

    // Table headers and data
    const tableHeaders = columns.map((col) => col.label);
    const tableData = data.map((item) =>
        columns.map((col) => {
            const val = col.accesor(item);
            return val !== null & val !== undefined ? String(val) : "";
        })
    );

    autoTable(doc, {
        startY: yPos + 2,
        head: [tableHeaders],
        body: tableData,
        theme: "plain",
        styles: {
            fillColor: cardBg,
            textColor: textWhite,
            fontSize: 8,
            cellPadding: 4,
            lineColor: [51, 51, 51],
            lineWidth: 0.1,
            font: "helvetica",
        },
        headStyles: {
            fillColor: headerBg,
            textColor: textMuted,
            fontSize: 7,
            fontStyle: "bold",
            textTransform: "uppercase",
        },
        alternateRowStyles: {
            fillColor: [20, 20, 20],
        },
        margin: { left: 14, right: 14 },
        // Footer on each page
        didDrawPage: (data) => {
            // Page number
            const pageCount = doc.internal.getNumberOfPages();
            doc.setTextColor(...textMuted);
            doc.setFontSize(7);
            doc.text(
                `Page ${data.pageNumber} of ${pageCount}`,
                pageWidth - 14,
                doc.internal.pageSize.getHeight() - 8,
                { align: "right" },
            );
            // App name in footer
            doc.text(
                "Money Manager",
                14,
                doc.internal.pageSize.getHeight() - 8
            );

            // Re-apply background on new pages
            if (data.pageNumber > 1) {
                doc.setFillColor(...darkBg);
                doc.rect(
                    0,
                    0,
                    pageWidth,
                    data.settings.margin.top,
                    "F"
                );
            }
        },
    });

    doc.save(`${filename}.pdf`);
    return true;
}

// PRE-BUILT EXPORT CONFIGS FOR EACH PAGE

export const EXPORT_CONFIGS = {
    transactions: {
        columns: [
            { label: "Date", accesor: (tx) => tx.date },
            { label: "Description", accesor: (tx) => tx.description || "-" },
            { label: "Category", accesor: (tx) => tx.category },
            {
                label: "Amount",
                accesor: (tx) =>
                    `$${parseFloat(tx.amount || 0).toFixed(2)}`,
            },
        ],
        getFilename: () =>
            `transactions_${new Date().toISOString().split('T')[0]}`,
        getTitle: () => "Transaction Report",
    },

    budgets: {
        columns: [
            { label: "Category", accesor: (b) => b.category },
            {
                label: "Budgeted",
                accesor: (b) =>
                    `$${parseFloat(b.amount || 0).toFixed(2)}`,
            },
            {
                label: "Spent",
                accesor: (b) =>
                    `$${parseFloat(b.spent || 0).toFixed(2)}`,
            },
            {
                label: "Remaining",
                accesor: (b) =>
                    `$${parseFloat(b.amount || 0) - parseFloat(b.spent || 0).toFixed(2)}`,
            },
            {
                label: "% Used",
                accesor: (b) =>
                    `${(b.percentUsed || 0).toFixed(1)}%`,
            },
            {
                label: "Status",
                accesor: (b) =>
                    b.is_recurring ? b.recurrence || "Yes" : "No",
            },
        ],
        getFilename: () =>
            `budgets_${new Date().toISOString().split('T')[0]}`,
        getTile: () => "Budget Report"
    },

    subscriptions: {
        columns: [
            { label: "Name", accesor: (s) => s.name },
            { label: "Category", accesor: (s) => s.category || "-" },
            {
                label: "Amount",
                accesor: (s) =>
                    `$${parseFloat(s.amount || 0).toFixed(2)}`,
            },
            {
                label: "Billing Cycle",
                accesor: (s) => s.billing_cycle || "-",
            },
            {
                label: "Status",
                accesor: (s) => s.status 
            },
            {
                label: "Next Payment",
                accesor: (s) => s.next_payment_date || "-",
            },
        ],
        getFilename: () =>
            `subscriptions_${new Date().toISOString().split('T')[0]}`,
        getTitle: () => "Subscription Report"
    },

    income: {
        columns: [
            { label: "Source", accesor: (inc) => inc.source },
            {
                label: "Amount",
                accesor: (inc) =>
                    `$${parseFloat(inc.amount || 0).toFixed(2)}`,
            },
            {
                label: "Date Received",
                accesor: (inc) => inc.period_start,
            },
            { label: "Period End", accesor: (inc) => inc.period_end },
        ],
        getFilename: () =>
            `income_${new Date().toISOString().split('T')[0]}`,
        getTitle: () => "Income Report",
    },
};
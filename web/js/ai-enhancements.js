// Enhanced AI with language detection and dynamic responses

// Language detection function
function detectLanguage(text) {
    const urduPattern = /[\u0600-\u06FF]/;
    const sindhiPattern = /[\u0600-\u06FF].*?(سنڌي|سندھی)/;
    const pashtoPattern = /[\u0600-\u06FF].*?(پښتو|پشتو)/;
    const punjabiPattern = /[\u0600-\u06FF].*?(پنجابی)/;
    
    if (sindhiPattern.test(text)) return 'sindhi';
    if (pashtoPattern.test(text)) return 'pashto';
    if (punjabiPattern.test(text)) return 'punjabi';
    if (urduPattern.test(text)) return 'urdu';
    return 'english';
}

// Multilingual responses
const translations = {
    urdu: {
        greeting: 'السلام علیکم! میں آپ کی کیسے مدد کر سکتا ہوں؟',
        payment_created: 'ادائیگی کی درخواست بنائی گئی',
        amount: 'رقم',
        order: 'آرڈر',
        reference: 'حوالہ نمبر',
        instructions: 'ہدایات',
        bank_details: 'بینک کی تفصیلات'
    },
    sindhi: {
        greeting: 'السلام عليڪم! آئون توهان جي ڪيئن مدد ڪري سگهان ٿو؟',
        payment_created: 'ادائگي جي درخواست ٺاهي وئي',
        amount: 'رقم',
        order: 'آرڊر',
        reference: 'حوالو نمبر',
        instructions: 'هدايتون',
        bank_details: 'بئنڪ جا تفصيل'
    },
    pashto: {
        greeting: 'السلام علیکم! زه څنګه ستاسو مرسته کولی شم؟',
        payment_created: 'د تادیې غوښتنه جوړه شوه',
        amount: 'مقدار',
        order: 'امر',
        reference: 'حواله شمیره',
        instructions: 'لارښوونې',
        bank_details: 'د بانک تفصیلات'
    },
    punjabi: {
        greeting: 'السلام علیکم! میں تہاڈی کیویں مدد کر سکدا ہاں؟',
        payment_created: 'ادائیگی دی درخواست بنائی گئی',
        amount: 'رقم',
        order: 'آرڈر',
        reference: 'حوالہ نمبر',
        instructions: 'ہدایتاں',
        bank_details: 'بینک دیاں تفصیلاں'
    },
    english: {
        greeting: 'Hello! How can I help you?',
        payment_created: 'Payment request created',
        amount: 'Amount',
        order: 'Order',
        reference: 'Reference',
        instructions: 'Instructions',
        bank_details: 'Bank Details'
    }
};

// Enhanced payment creation with bank details
async function createPaymentRequestEnhanced(orderId, amountPkr, lang = 'english') {
    const t = translations[lang] || translations.english;
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/payments/create`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                order_id: orderId,
                amount_pkr: amountPkr,
                payment_provider: selectedPaymentMethod
            })
        });

        if (!response.ok) {
            const errorText = await response.text();
            return `Payment API error (${response.status}): ${errorText}`;
        }

        const data = await response.json();
        
        // Bank details based on payment method
        let bankDetails = '';
        if (selectedPaymentMethod === 'jazzcash') {
            bankDetails = `\n\n**${t.bank_details}**\n- JazzCash Account: 03XX-XXXXXXX\n- Account Title: Your Business Name\n- CNIC: XXXXX-XXXXXXX-X`;
        } else if (selectedPaymentMethod === 'easypaisa') {
            bankDetails = `\n\n**${t.bank_details}**\n- EasyPaisa Account: 03XX-XXXXXXX\n- Account Title: Your Business Name\n- CNIC: XXXXX-XXXXXXX-X`;
        } else if (selectedPaymentMethod === 'bank_transfer') {
            bankDetails = `\n\n**${t.bank_details}**\n- Bank: ${data.meta?.bank_name || 'Your Bank'}\n- Account Title: ${data.meta?.account_title || 'Your Business'}\n- IBAN: ${data.meta?.iban || 'PK00XXXX0000000000000000'}\n- Branch Code: XXXX`;
        }
        
        return [
            `${t.payment_created} (${String(data.provider).toUpperCase()})`,
            '',
            `- **${t.order}**: ${orderId}`,
            `- **${t.amount}**: PKR ${Number(amountPkr).toLocaleString('en-PK', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`,
            `- **${t.reference}**: ${data.reference_id}`,
            `- **Status**: ${data.status}`,
            data.checkout_url ? `- **Checkout URL**: ${data.checkout_url}` : '',
            bankDetails,
            '',
            `**${t.instructions}**`,
            data.instructions
        ].filter(Boolean).join('\n');
    } catch (error) {
        return [
            'Could not reach payment API.',
            '',
            `- Ensure API is running at ${API_BASE_URL}`,
            `Error: ${error && error.message ? error.message : String(error)}`
        ].join('\n');
    }
}

// Extract amount from message intelligently
function extractAmount(message) {
    // Match patterns like: PKR 1000, Rs 1000, 1000 rupees, 1000 PKR
    const patterns = [
        /(?:PKR|Rs\.?|rupees?)\s*(\d+(?:,\d{3})*(?:\.\d{2})?)/i,
        /(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:PKR|Rs\.?|rupees?)/i,
        /(\d+(?:,\d{3})*(?:\.\d{2})?)/
    ];
    
    for (const pattern of patterns) {
        const match = message.match(pattern);
        if (match) {
            const amount = parseFloat(match[1].replace(/,/g, ''));
            if (amount > 0 && amount < 1000000) { // Reasonable range
                return amount;
            }
        }
    }
    return null;
}

// Localize response based on detected language
function localizeResponse(text, detectedLang) {
    const t = translations[detectedLang] || translations.english;
    
    if (detectedLang !== 'english') {
        return `[${detectedLang.toUpperCase()} Response]\n\n${text}`;
    }
    return text;
}

// Export for use in main script
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        detectLanguage,
        translations,
        createPaymentRequestEnhanced,
        extractAmount,
        localizeResponse
    };
}

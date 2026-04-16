import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const analyzeClaim = async (claimText: string) => {
    const response = await axios.post(`${API_URL}/analyze-claim`, {
        claim_text: claimText,
    });
    return response.data;
};

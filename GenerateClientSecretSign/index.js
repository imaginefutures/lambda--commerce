const bcrypt = require('bcryptjs');
const axios = require('axios');

exports.handler = async (event) => {
  try {
    console.log('GenerateClientSecretSign request received.');

    let body;
    try {
      body = typeof event.body === 'string' ? JSON.parse(event.body) : event.body;
    } catch (parseError) {
      throw new Error('body를 파싱할 수 없습니다.');
    }

    const clientId = body.client_id;
    const type = body.type;

    // ✅ 여기서부터가 핵심: raw/trim 로그 + trim 적용
    const clientSecretRaw = body.client_secret ?? "";
    const clientSecret = clientSecretRaw.trim();

    console.log('Token request payload validated.', {
      hasClientId: Boolean(clientId),
      hasClientSecret: Boolean(clientSecret),
      type,
    });

    if (!clientId) throw new Error('client_id가 전달되지 않았습니다.');
    if (!clientSecret) throw new Error('client_secret이 전달되지 않았습니다.');
    if (!type) throw new Error('type이 전달되지 않았습니다.');

    const timestamp = Date.now();

    const password = `${clientId}_${timestamp}`;

    // ✅ salt는 trim된 clientSecret 사용
    const hashed = bcrypt.hashSync(password, clientSecret);

    // ✅ base64는 Buffer로
    const clientSecretSign = Buffer.from(hashed, "utf8").toString("base64");

    const url = 'https://api.commerce.naver.com/external/v1/oauth2/token';
    const params = {
      client_id: clientId,
      timestamp: String(timestamp),
      grant_type: 'client_credentials',
      client_secret_sign: clientSecretSign,
      type, // SELF
    };

    try {
      const response = await axios.post(url, null, {
        params,
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      });

      console.log('Token request completed.', {
        hasAccessToken: Boolean(response.data?.access_token),
        expiresIn: response.data?.expires_in,
      });

      return {
        statusCode: 200,
        body: JSON.stringify(response.data),
      };
    } catch (apiError) {
      const status = apiError.response?.status || 500;
      const data = apiError.response?.data || null;

      console.error('API 요청 오류 status:', status);
      console.error('API 요청 오류 data:', JSON.stringify(data, null, 2));

      return {
        statusCode: status,
        body: JSON.stringify({
          result: 'API 요청 오류 발생',
          status,
          data,
        }),
      };
    }
  } catch (error) {
    console.error('오류 발생:', error);
    return {
      statusCode: 500,
      body: JSON.stringify({ result: '서버 내부 오류', error: error.message }),
    };
  }
};

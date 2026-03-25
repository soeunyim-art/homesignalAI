/**
 * AI 챗봇 테스트 스크립트
 *
 * 실행 방법:
 * 1. npm run dev로 Next.js 서버 시작
 * 2. 새 터미널에서: node test_chatbot.js
 */

const API_URL = 'http://localhost:3000/api/chat';

const testQuestions = [
  "동대문구 아파트 가격 전망은?",
  "최근 뉴스 요약해줘",
  "가장 상승률 높은 동은?",
];

async function testChatbot() {
  console.log('🧪 AI 챗봇 테스트 시작...\n');

  for (let i = 0; i < testQuestions.length; i++) {
    const question = testQuestions[i];
    console.log(`\n[테스트 ${i + 1}/${testQuestions.length}]`);
    console.log(`질문: ${question}`);
    console.log('─'.repeat(60));

    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: [
            { role: 'user', content: question }
          ]
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        console.error(`❌ 오류 (${response.status}):`, errorData.error);
        continue;
      }

      const data = await response.json();
      console.log(`✅ 응답 성공`);
      console.log(`\n답변:\n${data.message}\n`);

      if (data.usage) {
        console.log(`토큰 사용: 입력 ${data.usage.inputTokens}, 출력 ${data.usage.outputTokens}`);
      }
    } catch (error) {
      console.error(`❌ 네트워크 오류:`, error.message);
    }

    // API rate limit 방지
    if (i < testQuestions.length - 1) {
      console.log('\n⏳ 2초 대기 중...');
      await new Promise(resolve => setTimeout(resolve, 2000));
    }
  }

  console.log('\n\n✅ 테스트 완료!');
}

// 서버 연결 확인
async function checkServer() {
  console.log('🔍 Next.js 서버 확인 중...');
  try {
    const response = await fetch('http://localhost:3000', { method: 'HEAD' });
    if (response.ok) {
      console.log('✅ Next.js 서버 실행 중\n');
      return true;
    }
  } catch (error) {
    console.error('❌ Next.js 서버가 실행되지 않았습니다.');
    console.error('   먼저 "npm run dev"로 서버를 시작해주세요.\n');
    return false;
  }
  return false;
}

// 실행
checkServer().then(serverRunning => {
  if (serverRunning) {
    testChatbot();
  }
});

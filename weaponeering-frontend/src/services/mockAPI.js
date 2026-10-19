// Mock API Service
export const mockAPI = {
  // Target source options
  targetSources: [
    { id: 1, name: 'เป้าหมายร่วม', checked: false },
    { id: 2, name: 'เป้าหมาย ทอ.', checked: false },
    { id: 3, name: 'เป้าหมาย กกล.สุรนารี', checked: false },
    { id: 4, name: 'เป้าหมายทางลึก', checked: false },
    { id: 5, name: 'อื่นๆ', checked: false }
  ],

  // Target type options
  targetTypes: [
    'อาคาร',
    'สะพาน',
    'บังเกอร์',
    'คูเลน',
    'รันเวย์',
    'โรงเก็บเครื่องบิน',
    'เรือ',
    'เรดาร์',
    'คลังอาวุธ',
    'คลังเชื้อเพลิง'
  ],

  // Structure type options
  structureTypes: [
    'คอนกรีตเสริมเหล็ก',
    'คอนกรีต',
    'โครงเหล็ก',
    'ไม้',
    'ดิน',
    'อื่นๆ'
  ],

  // Strength level options
  strengthLevels: [
    'เปราะบาง',
    'แข็งแรง',
    'แข็งแรงพิเศษ'
  ],

  // Desired effect options
  desiredEffects: [
    'สิ้นสภาพ (Destroy)',
    'สูญเสียการควบคุม',
    'พังทลาย',
    'เสียหายบางส่วน'
  ],

  // Top 5 recommendations
  recommendations: [
    { id: 1, item: 'อาคาร', size: '2000 ปอนด์', qty: 3, pd: 0.85, pk: 0.92 },
    { id: 2, item: 'สะพาน', size: '1500 ปอนด์', qty: 2, pd: 0.78, pk: 0.88 },
    { id: 3, item: 'บังเกอร์', size: '1000 ปอนด์', qty: 4, pd: 0.82, pk: 0.90 },
    { id: 4, item: 'คูเลน', size: '500 ปอนด์', qty: 1, pd: 0.75, pk: 0.85 },
    { id: 5, item: 'รันเวย์', size: '250 ปอนด์', qty: 2, pd: 0.88, pk: 0.95 }
  ],

  // AI Analysis result text
  aiAnalysisText: `ผลการวิเคราะห์โดย AI:

1. ประสิทธิภาพการโจมตี: 85%
   - ความเสี่ยง: ต่ำ
   - ความเข้มข้น: สูง

2. ค่า CEP (Circular Error Probable): 20 เมตร
   - ความแม่นยำที่สูง

3. ค่า PK (Probability of Kill): 0.92
   - โอกาสการทำลายที่ดี

4. ข้อเสนอแนะ: เลือกเป้าหมายประเภท A เพื่อประสิทธิภาพสูงสุด`,

  // Mock chatbot responses
  getChatbotResponse: (message) => {
    const responses = [
      'ค่า CEP ปัจจุบัน: 20 เมตร โปรดระบุพิกัดลบลี่กรรมด้วย',
      'เป้าหมายนี้เหมาะสำหรับการโจมตีในเงื่อนไขอากาศปกติ',
      'ลองเพิ่มค่า PK โดยการเลือกเป้าหมายที่มีขนาดใหญ่ขึ้น',
      'ข้อมูลเชิงพื้นที่แสดงว่าพื้นที่นี้มีความเสี่ยงปานกลาง',
      'ระบบแนะนำการใช้อาวุธประเภท "แข็งแรงพิเศษ" สำหรับเป้าหมายนี้'
    ];
    return responses[Math.floor(Math.random() * responses.length)];
  },

  // Mock simulator video URL
  getSimulatorVideo: () => {
    return 'https://www.youtube.com/embed/dQw4w9WgXcQ';
  }
};

export default mockAPI;

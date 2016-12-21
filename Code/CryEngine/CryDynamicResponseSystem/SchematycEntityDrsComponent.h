// Copyright 2001-2016 Crytek GmbH / Crytek Group. All rights reserved.

#pragma once

#include <CrySerialization/Forward.h>
#include <Schematyc/Utils/GUID.h>

class CSchematycEntityDrsComponent final : public Schematyc::CComponent, DRS::IResponseManager::IListener, DRS::ISpeakerManager::IListener
{
public:

	struct SProperties
	{
		void Serialize(Serialization::IArchive& archive);

		string name;
	};

	struct SResponseStartedSignal
	{
		static Schematyc::SGUID ReflectSchematycType(Schematyc::CTypeInfo<SResponseStartedSignal>& typeInfo);

		int   m_signalId;
	};
	struct SResponseFinishedSignal
	{
		static Schematyc::SGUID ReflectSchematycType(Schematyc::CTypeInfo<SResponseFinishedSignal>& typeInfo);

		int   m_signalId;
		int   m_result;  //ProcessingResult_NoResponseDefined, ProcessingResult_ConditionsNotMet, ProcessingResult_Done, ProcessingResult_Canceled	
	};
	struct SLineStartedSignal
	{
		static Schematyc::SGUID ReflectSchematycType(Schematyc::CTypeInfo<SLineStartedSignal>& typeInfo);

		Schematyc::CSharedString  m_text;
		Schematyc::CSharedString  m_speakerName;
		//animation, audioTrigger... do we need these as well?
	};
	struct SLineEndedSignal
	{
		static Schematyc::SGUID ReflectSchematycType(Schematyc::CTypeInfo<SLineEndedSignal>& typeInfo);

		Schematyc::CSharedString  m_text;
		Schematyc::CSharedString  m_speakerName;
		bool    m_bWasCanceled ;
		//animation, audioTrigger... do we need these as well?
	};


	CSchematycEntityDrsComponent();
	~CSchematycEntityDrsComponent();

	// Schematyc::CComponent
	virtual bool Init() override;
	virtual void Run(Schematyc::ESimulationMode simulationMode) override;
	virtual void Shutdown() override;
	// ~Schematyc::CComponent

	// DRS::IResponseManager::IListener
	virtual void OnSignalProcessingStarted(SSignalInfos& signal, DRS::IResponseInstance* pStartedResponse) override;
	virtual void OnSignalProcessingFinished(SSignalInfos& signal, DRS::IResponseInstance* pFinishedResponse, eProcessingResult outcome) override;
	// ~DRS::IResponseManager::IListener

	// DRS::ISpeakerManager::IListener
	virtual void OnLineEvent(const DRS::IResponseActor* pSpeaker, const CHashedString& lineID, DRS::ISpeakerManager::IListener::eLineEvent lineEvent, const DRS::IDialogLine* pLine) override;
	// ~DRS::ISpeakerManager::IListener

	static Schematyc::SGUID ReflectSchematycType(Schematyc::CTypeInfo<CSchematycEntityDrsComponent>& typeInfo);
	static void             Register(Schematyc::IEnvRegistrar& registrar);


private:

	void SendSignal(const Schematyc::CSharedString& signalName, const Schematyc::CSharedString& contextFloatName, float contextFloatValue, const Schematyc::CSharedString& contextStringName, const Schematyc::CSharedString& contextStringValue);
	
	void SetFloatVariable(const Schematyc::CSharedString& collectionName, const Schematyc::CSharedString& variableName, float value);
	void SetStringVariable(const Schematyc::CSharedString& collectionName, const Schematyc::CSharedString& variableName, const Schematyc::CSharedString& value);
	void SetIntVariable(const Schematyc::CSharedString& collectionName, const Schematyc::CSharedString& variableName, int value);

	DRS::IVariableCollection* GetVariableCollection(const Schematyc::CSharedString& collectionName);

	DRS::IResponseActor* m_pDrsActor;
	//Schematyc::CConnectionScope            m_connectionScope;
};